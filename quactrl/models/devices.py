from dependency_injector import providers
from dependency_injector import containers
from quactrl.helpers import get_class


class DeviceContainer(containers.DynamicContainer):
    _strategies = {
        'singleton': providers.Singleton,
        'factory': providers.Factory,
        'thread_safe_sing': providers.ThreadSafeSingleton,
        'local_safe_sing': providers.ThreadLocalSingleton
    }

    def __init__(self, repository):
        super().__init__()
        self.repo = repository
        self.location = None

    def set_location(self, value):
        self.location = value
        names = self.repo.get_all_names_by_location(self.location)
        for name in names:
            self._inject_provider(name)

    def _inject_provider(self, dev_name):
        if not hasattr(self, dev_name):
            device = self.repo.get_by_name_location(dev_name, self.location)
            Provider = self._strategies[device.pop('_strategy', 'singleton')]
            DeviceClass = get_class(device.pop('class'))
            args = device.pop('_args', [])
            for index in range(len(args)):
                value = args[index]
                if type(value) is str and value[0] == '>':
                    args[index] = self._inject_provider(value[1:])
            kwargs = device
            for key in kwargs.keys():
                value = kwargs[key]
                if type(value) is str and value[0] == '>':
                    kwargs[key] = self._inject_provider(value[1:])

            setattr(self, dev_name, Provider(DeviceClass, *args,
                                             **kwargs))
        return getattr(self, dev_name)
