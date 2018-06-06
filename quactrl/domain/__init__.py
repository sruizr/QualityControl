from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.types import Integer, String
import importlib


Base = declarative_base()


class Abstract:
    """Hierarthical definition on is_a column"""
    is_a = Column(String(30))
    __mapper_args__ = {
        'polymorphic_on': is_a
    }


def get_component(name):
    modules = name.split('.')
    try:
        module = importlib.import_module('.'.join(modules[:-1]))
    except ValueError:
        return None

    return getattr(module, modules[-1], None)


class DeviceBase:
    def __init__(self, **pars):
        if pars:
            self.pars = pars
            for key, value in pars.items():
                setattr(self, key, value)

    def assembly(self, devices):
        if hasattr(self, 'connected_to'):
            for key, value in self.connected_to.items():
                if type(value) is list:
                    att_value = [devices[tracking] for tracking in value]
                else:
                    att_value = devices[value]
                setattr(self, key, att_value)
