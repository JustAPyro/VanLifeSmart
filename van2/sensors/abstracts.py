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


