from __future__ import annotations

from enum import Enum

from van2.sensors.abstracts import MalformedDataPointException, UnknownUnitException


def tcheck(name, variable, dtype):
    if not type(variable) == dtype:
        raise MalformedDataPointException(f'{name} must be a {dtype} not {type(variable)}')


class Time:
    def __init__(self, timestamp: float):
        tcheck('time', timestamp, float)
        self.posix = timestamp


class Distance:
    conversion_to_meters = {
        'meters': 1
    }

    def __init__(self, **kwargs):
        self.meters: float = 0

        for unit, distance in kwargs.items():
            if unit not in Distance.conversion_to_meters.keys():
                raise UnknownUnitException(f'No known conversion from {unit} to meters')

            if type(distance) != float and type(distance) != int:
                self.meters += distance * Distance.conversion_to_meters[unit]


class Text:
    def __init__(self, text: str):
        tcheck('Text', text, str)
        if ',' in text:
            raise MalformedDataPointException('Text cannot include commas')
        if '"' in text:
            raise MalformedDataPointException('Text cannot include double quotes')
        if 'null' in text:
            raise MalformedDataPointException('Text cannot contain "null"')
        if 'true' in text or 'false' in text:
            raise MalformedDataPointException('Text cannot contain "true" or "false"')
        self.text = text


class Number:
    def __init__(self, number: int):
        tcheck('Number', number, int)
        self.number = number


class Decimal:
    def __init__(self, decimal: float | int):
        if type(decimal) != float and type(decimal) != int:
            raise MalformedDataPointException('Decimal must be a float or int.')
        self.decimal = decimal


class DecimalNormalized(Decimal):
    def __init__(self, decimal: float):
        super().__init__(decimal)
        if not 0 <= decimal <= 1:
            raise MalformedDataPointException(f'DecimalNormalized received {decimal} but cannot be out of range 0-1')


class PositiveNumber(Number):
    def __init__(self, number: int):
        super().__init__(number)
        if number < 0:
            raise MalformedDataPointException('PositiveNumber was found less than zero')


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
