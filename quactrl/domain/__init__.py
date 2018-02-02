from sqlalchemy.ext.declarative import declarative_base
import importlib


Base = declarative_base()


def get_component(name):
    modules = name.split('.')
    try:
        module = importlib.import_module('.'.join(modules[:-1]))
    except ValueError:
        return None

    return getattr(module, modules[-1], None)


class DeviceBase:
    def __init__(self, pars=None):
        if pars:
            self.pars = pars

    def assembly(self, devices):
        connected_to = self.pars.get('connected_to')
        if connected_to:
            for key, value in connected_to.items():
                if type(value) is list:
                    att_value = [devices[tracking] for tracking in value]
                else:
                    att_value = devices[value]
                setattr(self, key, att_value)
