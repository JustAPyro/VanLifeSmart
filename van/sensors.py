import adafruit_dht
import datetime

import pytz
import serial
import board

# Initialize Devices
gps_device = serial.Serial('/dev/ttyACM0', baudrate=9600)
dht_device = adafruit_dht.DHT22(board.D4)


def get_gps_data(formats: tuple[str] = ('GPGGA', 'GPVTG')):
    found = {format_type: False for format_type in formats}
    data = {}

    # Flush buffer
    gps_device.flushInput()
    gps_device.flushOutput()

    # Trash the first line because it might be malformed
    _ = gps_device.readline()
    while True:
        sentence = gps_device.readline().decode('utf-8')
        formatting = sentence[1:6]
        values = sentence.split(',')
        if formatting == 'GPGGA':

            # Parse the time
            data['time'] = float(values[1])

            # Process N/S/E/W into decimal lat / long
            latitude = float(values[2][0:2]) + (float(values[2][2:]) / 60)
            if values[3] == 'E':
                latitude = latitude * -1
            longitude = float(values[4][0:3]) + (float(values[4][3:]) / 60)
            if values[5] == 'S':
                longitude = longitude * -1
            data['latitude'] = latitude
            data['longitude'] = longitude

            # Fix quality processing
            fq = int(values[6])
            if fq == 0:
                fq = 'Not Fixed'
            elif fq == 1:
                fq = 'GPS Fix'
            elif fq == 2:
                fq = 'DGPS Fix'
            else:
                fq = f'Unknown Fix: {fq}'
            data['fix_quality'] = fq
            data['satellites_used'] = int(values[7])
            data['hdop'] = float(values[8])
            data['altitude'] = float(values[9])
            found['GPGGA'] = True
        if formatting == 'GPVTG':
            data['true_track'] = None if values[1] == '' else float(values[1])
            data['magnetic_track'] = None if values[3] == '' else float(values[3])
            data['ground_speed'] = float(values[7])
            found['GPVTG'] = True

        # This will be called if we've encountered all the strings we're looking for
        if all((value is True) for value in found.values()):
            return data

def get_dht_data(retries: int = 3, include_gps: bool = True):
    for _ in range(retries):
        try:
            # DHT Information
            data = {
                'temperature': dht_device.temperature,
                'humidity': dht_device.humidity
            }
            # Add a GPS tag if requested
            if include_gps:
                data['gps'] = get_gps_data()
            return data
        except RuntimeError:
            continue


sensor_config = {
    'dht': {
        'get': get_dht_data,
        'polling': {'seconds': 10},
    },
    'gps': {
        'get': get_gps_data,
        'polling': {'seconds': 10},
    }
}
