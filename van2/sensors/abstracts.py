from abc import ABC, abstractmethod


class DataPoint(ABC):
    def __init__(self, fake: bool = False):
        self.fake = fake

    @abstractmethod
    def to_line(self) -> str:
        pass


class DataFactory(ABC):
    def __init__(self, development: bool = False):
        self.development = development

    @property
    @abstractmethod
    def data_type(self) -> str:
        pass

    @abstractmethod
    def get_data(self) -> DataPoint:
        pass


class MalformedDataPointException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class UnknownUnitException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
