from dependency_injector import providers
from dependency_injector import containers
from quactrl.helpers import get_class
from threading import Lock
from types import MethodType
from .core import Resource
import quactrl.models.quality as qua
import logging


logger = logging.getLogger(__name__)


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
        Device = model.Device
        args = getattr(model,'args', [])
        kwargs = getattr(model, 'kwargs', {})

        if cavity is None:
            return Device(self._conn(), *args, **kwargs)
        else:
            return Device(self._conn(cavity), *args, **kwargs)


class MultiplexedDutFactory(DutFactory):
    def __init__(self, conn_provider, multiplexor_factory):
        self.multiplexor_factory = multiplexor_factory
        super().__init__(conn_provider)

    def __call__(self, model, cavity):
        conn_index = (None if len(self.multiplexor_factory) == 1
                      else cavity // 8)

        dut = super().__call__(model, conn_index)
        return self.multiplexor_factory(dut, cavity)


class DeviceProvider(providers.Provider):
    """Provider of devices, with tracking attribute inserted
    """
    def __init__(self, Device, *args, **kwargs):
        "docstring"
        super().__init__()
        self.tracking = kwargs.pop('tracking', None)
        logger.debug('Creating device with tracking {}'.format(self.tracking))

        field = kwargs.pop('multi_dev_on', None)
        self._injectors = []
        if field is None:
            self._injectors.append(
                providers.ThreadSafeSingleton(Device, *args, **kwargs)
            )
        else:
            values = kwargs.pop(field)
            for value in values:
                new_kwargs = kwargs.copy()
                new_kwargs[field] = value
                self._injectors.append(
                    providers.ThreadSafeSingleton(Device, *args, **new_kwargs)
                )

    def __call__(self, cavity=None):
        cavity = 0 if cavity is None else cavity
        device = self._injectors[cavity]()
        device.tracking = self.tracking
        return device

    def __len__(self):
        return len(self._injectors)

class Toolbox(containers.DynamicContainer):
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

        self._devices = {}
        self._load_device_configs(devices)
        for name in self._devices.keys():
            self._inject_provider(name)

        if hasattr(self, 'dut_conn'):
            if hasattr(self, 'dut_multiplexor'):
                self.dut = MultiplexedDutFactory(self.dut_multiplexor(), self.dut_conn)
            else:
                self.dut = DutFactory(self.dut_conn)

    def _load_device_configs(self, devices):
        for device in devices:
            config = {'strategy': 'device',
                'class': device.model.class_name,
                'name': device.name}

            config['args'] = device.args
            kwargs = {'tracking': device.tracking}
            kwargs.update(device.kwargs)
            config['kwargs'] = kwargs

            self._load_component(config)

    def _load_component(self, config):
        name = config.get('name')
        args = config.get('args', [])
        for index, value in enumerate(args):
            args[index] = self._process_value(value)

        kwargs = config.get('kwargs', {})
        for key, value in kwargs.items():
            kwargs[key] = self._process_value(value)

        self._devices[name] = {
            'class': config.get('class'),
            'strategy': config.get('strategy', 'thread_safe_sing'),
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

    def _inject_provider(self, dev_name):
        if not hasattr(self, dev_name):
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
