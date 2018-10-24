import re
from dependency_injector import providers
from dependency_injector import containers
from quactrl.helpers import get_class


class DeviceModel:
    """Type of device, linked to a class with functionallity
    """
    def __init__(self, key, name, description=None, dev_class=None):
        "docstring"
        self.key = key
        self.name = name
        self.description = description
        self.dev_class = dev_class

    def get_class(self):
        return get_class(self.dev_class)


class Device:
    def __init__(self, device_model, tracking, location=None,
                 config_pars=None):
        self.model = device_model
        self.tracking = tracking
        self.config_pars = config_pars if config_pars else {}
        self.location = location

    @property
    def name(self):
        value = re.findall('(.*)>.*', self.tracking)
        if value:
            return value[0]

        return self.model.name


class DeviceContainer(containers.DynamicContainer):
    _strategies = {
        'singleton': providers.Singleton,
        'factory': providers.Factory,
        'thread_safe_sing': providers.ThreadSafeSingleton,
        'local_safe_sing': providers.ThreadLocalSingleton
    }

    def __init__(self, devices):
        super().__init__()
        self._devices = devices
        for name in devices.keys():
            self._inject_provider(name)

    def _inject_provider(self, dev_name):
        if not hasattr(self, dev_name):
            device = self._devices[dev_name]
            config = device.config_pars.copy()
            Provider = self._strategies[config.pop('_strategy', 'thread_safe_sing')]
            DeviceClass = device.model.get_class()
            args = config.pop('_args', [])
            for index in range(len(args)):
                value = args[index]
                if type(value) is str and value[0] == '>':
                    args[index] = self._inject_provider(value[1:])
            kwargs = config
            for key in kwargs.keys():
                value = kwargs[key]
                if type(value) is str and value[0] == '>':
                    kwargs[key] = self._inject_provider(value[1:])

            setattr(self, dev_name, Provider(DeviceClass, *args,
                                             **kwargs))
        return getattr(self, dev_name)
