from abc import ABC


class DataFactory(ABC):
    def __init__(self, development: bool = False):
        self.development = development

