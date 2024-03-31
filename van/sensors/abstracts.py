from abc import ABC, abstractmethod
from typing import Optional

from models import Base


class Sensor(ABC):
    def __init__(self, development: bool = False):
        self.development = development
        self.schedule_config = {
            'id': f'record_{self.data_type}',
            'description': f'Automatically scheduled for recording {self.data_type} sensor data.'
        }
        self.default_schedule = {'minutes': 1}

    @property
    @abstractmethod
    def data_type(self) -> str:
        pass

    @abstractmethod
    def get_data(self) -> Optional[Base]:
        pass

    def shutdown(self):
        pass


class MalformedDataPointException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class UnknownUnitException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
