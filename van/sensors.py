import adafruit_dht
import datetime
import requests
import os
import pytz
import serial
import board
import time

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
            gps_time = values[1].split('.')[0]
            if len(gps_time) < 6:
                gps_time = '0' + gps_time
            date = datetime.date.today()
            data['time'] = datetime.datetime(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=int(gps_time[0:2]),
                minute=int(gps_time[2:4]),
                second=int(gps_time[4:6]),
                tzinfo=datetime.timezone.utc
            ).timestamp()

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


def get_tio_data(latitude: float = None, longitude: float = None, arguments=None):
    data = {'gps': get_gps_data()}

    response = requests.get('https://api.tomorrow.io/v4/weather/realtime'
                            f'?location={latitude},{longitude}'
                            f'&apikey={os.environ["TOMORROWAPI"]}')

    td = response.json()['data']['values']
    # Parse time to unix timestamp, from format ex 2024-02-22T03:31:00Z (gmt)
    data['time'] = (datetime.datetime.strptime(response.json()['data']['time'], '%Y-%m-%dT%H:%M:%SZ')
                    .replace(tzinfo=datetime.timezone.utc)
                    .timestamp())

    data['uv_index'] = td['uvIndex']
    data['humidity'] = td['humidity']
    data['wind_gust'] = td['windGust']
    data['dew_point'] = td['dewPoint']
    data['cloud_base'] = td['cloudBase']
    data['wind_speed'] = td['windSpeed']
    data['visibility'] = td['visibility']
    data['cloud_cover'] = td['cloudCover']
    data['temperature'] = td['temperature']
    data['weather_code'] = td['weatherCode']
    data['cloud_ceiling'] = td['cloudCeiling']
    data['rain_intensity'] = td['rainIntensity']
    data['snow_intensity'] = td['snowIntensity']
    data['wind_direction'] = td['windDirection']
    data['sleet_intensity'] = td['sleetIntensity']
    data['uv_health_concern'] = td['uvHealthConcern']
    data['temperature_apparent'] = td['temperatureApparent']
    data['pressure_surface_level'] = td['pressureSurfaceLevel']
    data['freezing_rain_intensity'] = td['freezingRainIntensity']
    data['precipitation_probability'] = td['precipitationProbability']
    return data


sensor_config = {
    'dht': {
        'get': get_dht_data,
        'polling': {'seconds': 10},
    },
    'gps': {
        'get': get_gps_data,
        'polling': {'seconds': 10},
    },
    'tio': {
        'get': get_tio_data,
        'polling': {'minutes': 10},
    }

}
