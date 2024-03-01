from __future__ import annotations

from enum import Enum

from van2.sensors.abstracts import MalformedDataPointException, UnknownUnitException


def tcheck(name, variable, dtype):
    if not type(variable) == dtype:
        raise MalformedDataPointException(f'{name} must be a {dtype}')


class Time:
    def __init__(self, timestamp: float):
        tcheck('time', timestamp, float)
        self.posix = timestamp


class Distance:
    conversion_to_meters = {
        'meters'
    }

    def __init__(self, **kwargs):
        self.meters: float = 0

        for unit, distance in kwargs:
            if unit not in Distance.conversion_to_meters.keys():
                raise UnknownUnitException(f'No known conversion from {unit} to meters')

            if type(distance) != float and type(distance) != int:
                self.meters += distance * Distance.conversion_to_meters[unit]


class Text:
    def __init__(self, text: str):
        tcheck('Text', text, str)
        if ',' in text:
            MalformedDataPointException('Text cannot include commas')
        if '"' in text:
            MalformedDataPointException('Text cannot include double quotes')
        self.text = text


class GPSFixQuality(Text):
    def __init__(self, text):
        super().__init__(text)
        if text not in (
                'FAKE',
                'Not Fixed',
                'GPS Fix',
                'DGPS Fix'
        ):
            raise MalformedDataPointException(f'Unknown GPS Fix: {text}')


class Coordinates:
    def __init__(self, latitude: float, longitude: float):

        tcheck('latitude', latitude, float)

        if not type(longitude) == float:
            raise MalformedDataPointException(f'Longitude must be a float')

        if not -90 < latitude < 90:
            raise MalformedDataPointException(f'Latitude must be between -90 and 90')

        if not -180 < longitude < 180:
            raise MalformedDataPointException(f'Longitude must be between -180 and 180')

        self.latitude = latitude
        self.longitude = longitude
