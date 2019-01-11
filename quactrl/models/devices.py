import re
from dependency_injector import providers
from dependency_injector import containers
from quactrl.helpers import get_class
from threading import Lock
from types import MethodType


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
        if '_name' in self.config_pars:
            return self.config_pars['_name'][1:]

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
            if device.tracking:
                kwargs['tracking'] = device.tracking

            device_ =  Provider(DeviceClass, *args, **kwargs)
            setattr(self, dev_name, device_)

        return getattr(self, dev_name)


class DeviceRack(list):
    """Not thread safe list of devices
    """
    def __init__(self, *devices):
        super().__init__(devices)



class ExclusiveDeviceRack(DeviceRack):
    """List of devices where one can not execute method when other
    is executing
    """
    def __init__(self, *devices):
        self._lock = Lock()
        elements = [LocableDecorator(device, self._lock)
                    for device in devices
        ]
        super().__init__(*elements)


class LockableDecorator:
    def __init__(self, decorated, lock):
        self._lock = lock
        self._decorated = decorated

    def __getattr__(self, name):
        def locking(attr):
            def method(*args, **kwargs):
                with self._lock:
                    result = attr(*args, **kwargs)
                return result
            return method

        if name[0] != '_':  # Private attributes are not get from decorated object
            attr = getattr(self._decorated, name)
            if type(attr) is MethodType:
                return locking(attr)
            return attr

    def __setattr__(self, name, value):
        """New attributes are stored in decorator
        """
        if hasattr(self._decorated, name):
            setattr(self._decorated, name, value)
        else:
            setattr(self, name, value)
