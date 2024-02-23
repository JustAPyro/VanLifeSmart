import adafruit_dht
import datetime
import requests
import os
import pytz
import serial
import board
import time
from gps import GPSManager
from abc import ABC, abstractmethod

# Initialize Devices
gps = GPSManager()
dht_device = adafruit_dht.DHT22(board.D4)


class AbstractSensor(ABC):
    def __init__(self, default_schedule):
        self._default_schedule = default_schedule

    @abstractmethod
    @property
    def default_schedule(self):
        return self._default_schedule

    @abstractmethod
    @property
    def sensor_type(self) -> str:
        pass

    @abstractmethod
    def get_data(self):
        pass


class TIO(AbstractSensor):
    def __init__(self, default_schedule: dict, **kwargs):
        super().__init__(**kwargs)

    def sensor_type(self) -> str:
        return 'tio'

    def default_schedule(self):
        return self._default_schedule

    def get_data(self):
        data = {'gps': get_gps_data()}

        response = requests.get('https://api.tomorrow.io/v4/weather/realtime'
                                f'?location={data["gps"]["latitude"]},{data["gps"]["latitude"]}'
                                f'&apikey={os.environ["TOMORROWAPI"]}')
        if response.status_code != 200:
            print('ERROR:', response)  # TODO: Log this
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


class DHT(AbstractSensor):
    def __init__(self, pin, retries: int = 3, include_gps: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.retries = retries
        self.include_gps = include_gps
        self.dht_device = adafruit_dht.DHT22(pin)

    @property
    def sensor_type(self) -> str:
        return 'dht'

    def get_data(self):
        for _ in range(self.retries):
            try:
                # DHT Information
                data = {
                    'temperature': dht_device.temperature,
                    'humidity': dht_device.humidity
                }
                # Add a GPS tag if requested
                if self.include_gps:
                    data['gps'] = get_gps_data()
                return data
            except RuntimeError:
                continue


class GPS(AbstractSensor):
    def __init__(self, location: str = '/dev/ttyACM0', baud: int = 9600, **kwargs):
        super().__init__(**kwargs)
        self.gps = GPSManager(location, baud)

    @property
    def sensor_type(self) -> str:
        return 'gps'

    def get_data(self):
        return self.gps.get_dict([
            'time',
            'latitude',
            'longitude',
            'fix_quality',
            'satellites_used',
            'hdop',
            'altitude',
            'true_track',
            'magnetic_track',
            'ground_speed'
        ])


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
                            f'?location={data["gps"]["latitude"]},{data["gps"]["latitude"]}'
                            f'&apikey={os.environ["TOMORROWAPI"]}')
    if response.status_code != 200:
        print('ERROR:', response)  # TODO: Log this
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


sensors: list[AbstractSensor] = [
    GPS(location='/dev/ttyACM0', baud=9600,
        default_schedule={'seconds': 10}),
    #DHT(pin=board.D4, retries=3, include_gps=True,
    #    default_schedule={'seconds': 15}),
    #TIO(default_schedule={'seconds': 15})
]

sensor_config = {
    'dht': {
        'get': get_dht_data,
        'polling': {'minutes': 10},
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
