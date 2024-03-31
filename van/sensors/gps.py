import logging
import threading
import datetime
from typing import Optional

import serial
from serial import SerialException

from models import GPSData
from van.sensors.abstracts import Sensor

logger = logging.getLogger(__name__)


class GPS(Sensor):
    def __init__(self, location: str = '/dev/ttyACM0', baud: int = 9600, development: bool = False, **kwargs):
        super().__init__(development=development, **kwargs)

        # The following code tries to launch the GPSManager using specified location and baud
        # If it can not it will either switch to fake data is development is true, otherwise raise an exception
        self.manager: Optional[GPSManager] = None
        try:
            self.manager = GPSManager(location, baud)
            logger.info(f'Successfully launched GPSManager at location "{location}" and baud "{baud}"')
        except SerialException as exception:
            if development:
                logger.warning('Launched GPSManager in development mode because of serial exception; '
                               'Unit will produce fake values.')
            else:
                # If we're not in development and still can't open the GPS continue the exception
                raise exception

    @property
    def data_type(self):
        return 'gps'

    def get_data(self) -> Optional[GPSData]:
        if self.manager:
            return GPSData(**self.manager.get_dict([
                'latitude',
                'longitude',
                'altitude',
                'fix_quality',
                'satellites_used',
                'hdop',
                'true_track',
                'magnetic_track',
                'ground_speed'
            ]))

        # Otherwise we need to return a fake data point
        return GPSData(
            latitude=41.618950,
            longitude=-85.826400,
            altitude=3,
            fix_quality='FAKE',
            satellites_used=0,
            hdop=0,
            true_track=None,
            magnetic_track=None,
            ground_speed=None,
        )

    def shutdown(self):
        if self.manager:
            self.manager.stop()

class GPSManager:
    unimplemented_formats = ('GPGSA', 'GPGSV', 'GPGLL', 'GPTXT', 'GPRMC')
    fix_quality_codes = {
        0: 'Not Fixed',
        1: 'GPS Fix',
        2: 'DGPS Fix'
    }
    identifiers = {
        'GA': {
            'short': 'Galileo',
            'long': 'European Global Navigation System',
            'region': 'Europe'
        },
        'GB': {
            'short': 'BDS',
            'long': 'BeiDou Navigation Satellite System',
            'region': 'China'
        },
        'GI': {
            'short': 'NavIC',
            'long': 'Indian Regional Navigation Satellite System',
            'region': 'India'
        },
        'GL': {
            'short': 'GLONASS',
            'long': 'Globalnaya Navigatsionnaya Sputnikovaya Sistema',
            'region': 'Russia'
        },
        'GN': {
            'short': 'GNSS',
            'long': 'Global Navigation Satellite System',
            'region': 'Multiple'
        },
        'GP': {
            'short': 'GPS',
            'long': 'Global Positioning System',
            'region': 'United States'
        },
        'GQ': {
            'short': 'QZSS',
            'long': 'Quasi-Zenith Satellite System',
            'region': 'Japan'
        }
    }

    def __init__(self, location: str = '/dev/ttyACM0', baud: int = 9600):
        self._running = True
        self.data = {} 

        # Create the gps serial connection and flush/clear buffer
        self._gps = serial.Serial(location, baud)

        gps_thread = threading.Thread(target=self.listen)
        gps_thread.start()

    def listen(self):
        # Flush the inputs and outputs
        self._gps.flushInput()
        self._gps.flushOutput()

        # First line can be corrupt
        try:
            _ = self._gps.readline()
            while self._running:
                sentence = self._gps.readline().decode('utf-8')
                self._parse_sentence(sentence)
        except (Exception,) as e:
            raise e

    def _parse_sentence(self, sentence: str):
        words = sentence.split(',')
        formatting = words.pop(0)[1:]
        now = datetime.datetime.now()
        if formatting == 'GPGGA':
            source = 'GPGGA'
            # Parse the time
            gps_time = words[0].split('.')[0]
            if len(gps_time) < 6:
                gps_time = '0' + gps_time
            date = datetime.date.today()
            t = datetime.datetime(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=int(gps_time[0:2]),
                minute=int(gps_time[2:4]),
                second=int(gps_time[4:6]),
                tzinfo=datetime.timezone.utc
            ).timestamp()
            self.data['time'] = (t, now, source)

            # Process N/S/E/W into decimal lat / long
            latitude = float(words[1][0:2]) + (float(words[1][2:]) / 60)
            if words[2] == 'S':
                latitude = latitude * -1
            longitude = float(words[3][0:3]) + (float(words[3][3:]) / 60)
            if words[4] == 'W':
                longitude = longitude * -1
            self.data['latitude'] = (latitude, now, source)
            self.data['longitude'] = (longitude, now, source)

            # Process the signal quality
            fix_quality = words[5]
            if int(fix_quality) in GPSManager.fix_quality_codes:
                fix_quality = GPSManager.fix_quality_codes[int(fix_quality)]
            self.data['fix_quality'] = (fix_quality, now, source)
            self.data['satellites_used'] = (int(words[6]), now, source)
            self.data['hdop'] = (float(words[7]), now, source)
            self.data['altitude'] = (float(words[8]), now, source)

        elif formatting == 'GPVTG':
            source = 'GPVTG'
            self.data['true_track'] = (None if words[0] == '' else float(words[0]), now, source)
            self.data['magnetic_track'] = (None if words[2] == '' else float(words[2]), now, source)
            self.data['ground_speed'] = (None if words[6] == '' else float(words[6]), now, source)
        elif formatting in GPSManager.unimplemented_formats:
            pass
        else:
            logger.warning(f'ATTENTION: Unseen NMEA Format: {formatting}')

    def get_dict(self, items: list[str]):
        return {item: self.data[item][0] for item in items if item in self.data}

    def stop(self):
        self._running = False
        self._gps.close()
