from abc import ABC, abstractmethod


class DataFactory(ABC):
    def __init__(self, development: bool = False):
        self.development = development

    @property
    @abstractmethod
    def data_type(self) -> str:
        pass

    @abstractmethod
    def get_data(self) -> dict:
        pass


class DataPoint(ABC):
    def __init__(self, fake: bool = False):
        self.fake = fake

    @abstractmethod
    def to_line(self) -> str:
        pass


class MalformedDataPointException(Exception):
    def __init__(self, msg):
        super().__init__(msg)