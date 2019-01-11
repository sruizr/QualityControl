import re
from dependency_injector import providers
from dependency_injector import containers
from quactrl.helpers import get_class
from threading import Lock
from types import MethodType


class DeviceModel:
    """Type of device, linked to a class with functionallity
    """
    def __init__(self, key, name, description=None, pars=None):
        "docstring"
        self.key = key
        self.name = name
        self.description = description
        self.pars = pars if pars else {}

    @property
    def class_name(self):
        return self.pars['class']


class Device:
    def __init__(self, device_model, tracking, location=None,
                 pars=None):
        self.model = device_model
        self.tracking = tracking
        self.location = location
        self.pars = pars if pars else {}

    @property
    def name(self):
        return  self.pars.get('name', self.model.name)

    @property
    def args(self):
        return self.pars.get('args', [])

    @property
    def kwargs(self):
        return self.pars.get('kwargs', {})


class DeviceProvider(providers.ThreadSafeSingleton):
    def __init__(self, Device, *args, **kwargs):
        "docstring"
        args = list(args)
        self.tracking = args.pop(0)
        print('Device is {}'.format(Device))
        super().__init__(Device, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        device = super().__call__(*args, **kwargs)
        if not hasattr(device, 'tracking'):
            device.tracking = self.tracking
        return device


class DeviceContainer(containers.DynamicContainer):
    _providers = {
        'singleton': providers.Singleton,
        'factory': providers.Factory,
        'thread_safe_sing': providers.ThreadSafeSingleton,
        'local_safe_sing': providers.ThreadLocalSingleton,
        'device': DeviceProvider
    }

    def __init__(self, devices):
        """Receive a list of devices and loads a container of them and subcomponents
        """
        super().__init__()
        self._devices = {}
        self._load_device_configs(devices)
        for name in self._devices.keys():
            self._inject_provider(name)

    def _load_device_configs(self, devices):
        for device in devices:
            config = {'strategy': 'device', 'class': device.model.class_name,
                      'name': device.name}
            args = [device.tracking]
            args.extend(device.args)
            config['args'] = args

            kwargs = {}
            kwargs.update(device.kwargs)
            if kwargs:
                config['kwargs'] = kwargs

            self._load_component(config)


    def _load_component(self, config):
        name = config.pop('name')
        args = config.pop('args', [])
        for index, value in enumerate(args):
            args[index] = self._process_value(value)

        kwargs = config.pop('kwargs', {})
        for key, value in kwargs.items():
            kwargs[key] = self._process_value(value)


        self._devices[name] = {
            'class': config.get('class'),
            'strategy': config.get('strategy', 'thread_safe_sing'),
            'args': args,
            'kwargs:': kwargs,
        }

    def _process_value(self, value):
        if (type(value) is dict) and ('class' in value) and ('name' in value):
            self._load_component(value)
            return '>' + value['name']
        else:
            return value

    def _inject_provider(self, dev_name):
        print(self._devices)
        config = self._devices[dev_name]

        Provider = self._providers[config['strategy']]
        DeviceClass = get_class(config['class'])

        args = config.get('args', [])
        for index, value in enumerate(args):
            if type(value) is str and value and value[0] == '>':
                args[index] = self._inject_provider(value[1:])

        kwargs = config.get('kwargs', {})
        for key in kwargs.keys():
            value = kwargs[key]
            if type(value) is str and value and value[0] == '>':
                kwargs[key] = self._inject_provider(value[1:])

        setattr(self, dev_name, Provider(DeviceClass, *args, **kwargs))

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
