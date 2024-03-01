from typing import Optional

import datetime
import requests
import os
import pytz
import serial

import time
from gps import GPSManager
from abc import ABC, abstractmethod

try:
    import adafruit_dht
    import board
    dht_enabled = True
except ImportError:
    adafruit_dht = None
    board = None
    dht_enabled = False




class AbstractSensor(ABC):
    """
    Defines the abstract interface that a sensors must implement to be
    included in the local server. A sensors inheriting from this can be
    added to the sensors list at the bottom of this file and the following
    will then happen automatically.

    1. A section of payload will be dedicated to this sensors.
    2. A scheduler will be assigned to log data from this sensors
        to payload[{sensor_type}] based on the interval provided in
        the default_schedule dict.

    3. On application exit the sensors shutdown() method will fire
        giving the sensors a chance to close anything it needs to.
    """
    def __init__(self, default_schedule):
        self.default_schedule = default_schedule

    def shutdown(self):
        """
        This method will get called on all sensors before application shutdown.
        Override it to do things like close ports and files for a sensors.
        """
        pass

    @property
    @abstractmethod
    def sensor_type(self) -> str:
        """Returns a string representing the type of sensors."""
        pass

    @property
    @abstractmethod
    def sensor_description(self) -> str:
        """Returns a string description of what the sensors records"""
        pass

    @abstractmethod
    def get_data(self) -> dict:
        """Returns a dict of data retrieved from the sensors"""
        pass

    @abstractmethod
    def from_csv(self, line: str) -> dict:
        """Parses a CSV line into a dict data object"""
        pass


class TIO(AbstractSensor):
    def __init__(self, default_schedule: dict, **kwargs):
        super().__init__(**kwargs)

    def sensor_type(self) -> str:
        return 'tio'

    def default_schedule(self):
        return self._default_schedule

    def get_data(self):
        data = {'gps': 'get_gps_data()'}

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
        self.dht = adafruit_dht.DHT22(pin)

    @property
    def sensor_type(self) -> str:
        return 'dht'

    def get_data(self):
        for _ in range(self.retries):
            try:
                # DHT Information
                data = {
                    'temperature': self.dht.temperature,
                    'humidity': self.dht.humidity
                }
                # Add a GPS tag if requested
                if self.include_gps:
                    data['gps'] = "get_gps_data()"
                return data
            except RuntimeError:
                continue

    def from_csv(self, line: str) -> dict:
        vals = line.strip().split(',')
        return {

        }


class GPS(AbstractSensor):
    """USB GPS sensors"""
    def __init__(self, location: str = '/dev/ttyACM0', baud: int = 9600, **kwargs):
        # Call super and then instantiate a GPS manager with given location and baud rate
        super().__init__(**kwargs)
        self.gps = GPSManager(location, baud)

    def shutdown(self):
        self.gps.stop()

    @property
    def sensor_type(self) -> str:
        return 'gps'

    @property
    def sensor_description(self) -> str:
        return 'Records positional and navigational satellite data'

    def get_data(self):
        return self.gps.get_dict([
            'time',
            'latitude',
            'longitude',
            'altitude',
            'fix_quality',
            'satellites_used',
            'hdop',
            'true_track',
            'magnetic_track',
            'ground_speed'
        ])

    # TODO: This is very dangerous since ordering isn't guaranteed
    def from_csv(self, line: str) -> Optional[dict]:
        vals = line.strip().split(',')
        # If this doesn't have the right number of
        #csv values we return None
        if len(vals) != 10:
            return None
        try:
             return {
                'time': float(vals[0]),
                'latitude': float(vals[1]),
                'longitude': float(vals[2]),
                'altitude': float(vals[3]),
                'fix_quality': str(vals[4]),
                'satellites_used': int(vals[5]),
                'hdop': float(vals[6]),
                'true_track': None if vals[7] == 'None' else float(vals[7]),
                'magnetic_track': None if vals[8] == 'None' else float(vals[8]),
                'ground_speed': None if vals[9] == 'None' else float(vals[9]),
            }
        except (Exception,):
            raise Exception


def get_tio_data(latitude: float = None, longitude: float = None, arguments=None):
    data = {'gps': 'TODO'}

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

