from dependency_injector import providers
from dependency_injector import containers
from quactrl.helpers import get_class
from threading import Lock
from types import MethodType
from .core import Resource
import quactrl.models.quality as qua
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DeviceModel(Resource):
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


class AutomaticTestEquipment:
    def __init__(self, **components):
        for name, component in components.items():
            setattr(self, name, component)


class Device(qua.Subject):
    """Implementation of device
    """
    def __init__(self, device_model, tracking, pars=None):
        super().__init__()

        self.model = device_model
        self.tracking = tracking
        self.pars = pars if pars else {}

    @property
    def name(self):
        return self.pars.get('name', self.model.name)

    @property
    def args(self):
        return self.pars.get('args', [])

    @property
    def kwargs(self):
        return self.pars.get('kwargs', {})


class DutFactory:
    def __init__(self, conn_provider):
        self._conn = conn_provider

    def __call__(self, model, cavity=None):
        Dut, args, kwargs = model.get_device_pars()
        return Dut(self._conn(cavity), *args, **kwargs)

# class MultiplexedDutFactory(DutFactory):
#     def __init__(self, conn_provider, multiplexor_factory):
#         self.multiplexor_factory = multiplexor_factory
#         super().__init__(conn_provider)

#     def __call__(self, model, cavity):
#         conn_index = (None if len(self.multiplexor_factory) == 1
#                       else cavity // 8)

#         dut = super().__call__(model, conn_index)
#         return self.multiplexor_factory(dut, cavity)


class DeviceProvider(providers.Provider):
    """Provider of devices, with tracking attribute inserted
    """
    def __init__(self, Device, *args, **kwargs):
        "docstring"
        super().__init__()
        self.tracking = kwargs.pop('tracking', None)
        logger.debug('Creating device with tracking {}'.format(self.tracking))

        self._injector = providers.Singleton(Device, *args, **kwargs)

    def __call__(self):
        device = self._injector()
        device.tracking = self.tracking
        return device


class Toolbox:
    def __init__(self, devices):
        "docstring"

        container = DeviceContainer(devices)
        for device in devices:
            setattr(self, device.name,
                    getattr(container, device.name)())

        if hasattr(self, 'ate') and hasattr(self.ate, 'dut_conn'):
            self.dut_factory = DutFactory(self.ate.dut_conn)


class DeviceContainer(containers.DynamicContainer):
    """Container of devices and its components
    """
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
        logger.info('Composing {} devices'.format(len(devices)))
        super().__init__()

        self._components = {}
        self._load_device_configs(devices)
        for name in self._components.keys():
            self._inject_provider(name)

    def _load_device_configs(self, devices):
        self.devices = {}
        for device in devices:
            config = {'strategy': 'device',
                'class': device.model.class_name,
                'name': device.name}

            config['args'] = device.args
            kwargs = {'tracking': device.tracking}
            kwargs.update(device.kwargs)
            config['kwargs'] = kwargs

            self.devices[device.name] =None
            self._load_component(config)

    def _load_component(self, config):
        name = config.get('name')
        args = config.get('args', [])
        for index, value in enumerate(args):
            args[index] = self._process_value(value)

        kwargs = config.get('kwargs', {})
        for key, value in kwargs.items():
            kwargs[key] = self._process_value(value)

        self._components[name] = {
            'class': config.get('class'),
            'strategy': config.get('strategy', 'singleton'),
            'name': name,
            'args': args,
            'kwargs': kwargs,
        }

    def _process_value(self, value):
        if (type(value) is dict) and ('class' in value) and ('name' in value):
            self._load_component(value)
            return '>' + value['name']
        else:
            return value

    def _inject_provider(self, name):
        if not hasattr(self, name):
            config = self._components[name]

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

            setattr(self, name, Provider(DeviceClass, *args, **kwargs))

        return getattr(self, name)


class DeviceRack(list):
    """Not thread safe list of devices
    """
    def __init__(self, *devices):
        super().__init__(devices)


class LockableDecorator:
    """Decorator with capacities of locking other when a method is executed
    """
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

        if name[0] != '_':
            #  Private attributes are not get from decorated object
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


class ExclusiveDeviceRack(DeviceRack):
    """List of devices where one can not execute method when other
    is executing
    """
    def __init__(self, *devices):
        self._lock = Lock()
        elements = [LockableDecorator(device, self._lock)
                    for device in devices]
        super().__init__(*elements)
