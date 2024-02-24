import serial
import threading
import time
import logging
import datetime

logger = logging.getLogger(__name__)


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
        self._gps = serial.Serial('/dev/ttyACM0', baudrate=9600)

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
            pass

    def _detect_corruption(self, sentence: str) -> bool:
        """
        Returns True if we detect corruption or bad formatting in this sentence.
        Will cause the sentence to be ignored.
        """
        # All valid NMEA sentences start with $
        if sentence[0] != '$':
            return True
        if sentence[1:3] not in GPSManager.identifiers.keys():
            return True
        return False

    def _parse_sentence(self, sentence: str):
        # Causes bugs?
        # If this seems to be corrupted we just skip it
        #if self._detect_corruption(sentence):
        #    logger.info(f'Ignoring sentence with likely corruption: {sentence}')
        #    return

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
            if words[2] == 'E':
                latitude = latitude * -1
            longitude = float(words[3][0:3]) + (float(words[3][3:]) / 60)
            if words[4] == 'S':
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
            self.data['ground_speed'] = (float(words[6]), now, source)
        elif formatting in GPSManager.unimplemented_formats:
            pass
        else:
            logger.warning(f'ATTENTION: Unseen NMEA Format: {formatting}')

    def get_dict(self, items: list[str]):
        return {item: self.data[item][0] for item in items if item in self.data}

    def stop(self):
        self._running = False
        self._gps.close()


if __name__ == '__main__':
    x = GPSManager()
    for _ in range(60):
        time.sleep(1)
        print(x.get_dict(['latitude', 'longitude']))
    x.running = False
