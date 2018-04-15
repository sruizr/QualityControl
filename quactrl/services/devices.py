from queue import Queue
import types
from threading import Thread, Lock
from quactrl.helpers import get_class


class Device:
    def __init__(self, **pars):
        if pars:
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


class DeviceManager:
    def __init__(self, workers=1):
        self.orders = Queue()
        self.workers = [Worker(self) for _ in range]
        self.devices = {}
        for worker in self.workers:
            worker.start()

    def add_device(self, name, pars):
        dev_pars = pars.copy()
        Device = get_class(dev_pars.pop('class_name'))
        device = Device(**dev_pars)
        device_proxy = DeviceProxy(device, self)
        if name in self.devices.keys():
            if type(self.devices[name]) is not list:
                self.devices[name] = [self.devices[name]]
            self.devices[name].append(device_proxy)
        else:
            self.devices[name] = device_proxy

    def stop(self):
        for worker in self.workers:
            worker._stop = True
        for _ in range(len(self.workers)):
            self.orders.put(None)


class DeviceProxy:
    def __init__(self, implementation, device_manager):
        self.lock = Lock()
        self.manager = device_manager
        self._impl = implementation
        self._answer = Queue()

    def __getattr__(self, name):
        if hasattr(self._impl, name):
            self._method = getattr(self._impl, name)
            if (
                name != 'assembly' or
                isinstance(self._method, types.MethodType)
            ):
                return self._method
            else:
                return self._exec

        raise AttributeError()

    def _exec(self, *args, **kwargs):
        self.manager.orders.put(
            (self, self._method, args, kwargs)
        )
        answer = self._answer.get()
        if type(answer) is Exception:
            raise answer
        return answer


class Worker(Thread):
    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        self._stop = False

    def run(self):
        while not self._stop:
            self.cycle()

    def cycle(self):
        order = self.device_manager.orders.get()
        if order is None:
            self._stop = True
        else:
            client, method, args, kwargs = order
            with client.lock:
                try:
                    answer = method(*args, **kwargs)
                except Exception as e:
                    answer = e
                client.answer.put(answer)
