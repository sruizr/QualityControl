from abc import ABC, abstractmethod


class Entity(ABC):
    _no_persist = []

    @abstractmethod
    def convert_to_dict(self, level=1):
        raise NotImplementedError()

    @abstractmethod
    def create_from_dict(self, dict_obj):
        raise NotImplementedError()
