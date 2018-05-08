from queue import Queue
import types
from abc import ABC, abstractmethod
from threading import Thread, Lock
from quactrl.helpers import get_class
from quactrl.domain.data import dal


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
    """Thread safe manager of a repository of devices"""
    def __init__(self):
        self.devices = {}
        self.lock = Lock()

    def __getitem__(self, key):
        return self.devices[key]

    def __setitem__(self, key, value):
        self.devices[key] = value

    def load_devs_from(self, location_key):
        db_devices = dal.get_devices_by(location_key=location_key)

        self.devices = {}  # Clearing previous loading
        for db_device in db_devices:
            pars = db_device.pars.copy()
            pars['tracking'] = db_device.tracking
            pars['name'] = db_device.resource.name

            device = self.create_device(pars)
            name = device.name
            if name in self.devices.keys():
                if type(self.devices[name]) is not dict:
                    first_dev = self.devices[name]
                    self.devices[name] = {first_dev.tracking: first_dev}
                self.devices[name][device.tracking] = device
            else:
                self.devices[name] = device

    def assembly_all(self):
        devices_by_tracking = {}
        for device in self.devices:
            devices_by_tracking[device.tracking] = device

        for device in self.devices:
            device.assembly(devices_by_tracking)

    def create_device(self, pars):
        class_name = pars.pop('class_name')
        Device = get_class(class_name)
        device = Device(**pars)

        return DeviceProxy(device, self)


# class ThreadPoolDeviceManager(DeviceManager):
#     def __init__(self, workers=1):
#         super().__init__()
#         self._orders = Queue()
#         self._workers = [Worker(self) for _ in range]
#         for worker in self._workers:
#             worker.start()

#     def create_device(self, pars):
#         dev_pars = pars.copy()
#         Device = get_class(dev_pars.pop('class_name'))
#         device = Device(**dev_pars)
#         device_proxy = DeviceProxy(device, self)
#         return device_proxy

#     def stop(self):
#         for _ in range(len(self.workers)):
#             self.orders.put(None)

#     def __del__(self):
#         """Closes all internal worker's threads"""
#         self.stop()


class DeviceProxy:
    def __init__(self, implementation, device_manager):
        self.lock = Lock()
        self.manager = device_manager
        self._impl = implementation

    def __getattr__(self, name):

        if hasattr(self._impl, name):
            self._method = getattr(self._impl, name)
            if (name == 'assembly' or
                not isinstance(self._method, types.MethodType)
            ):
                return self._method
            else:
                return self._exec

        raise AttributeError()

    def _exec(self, *args, **kwargs):

        with self.lock:
            result = self._method(*args, **kwargs)
        return result


# class Worker(Thread):
#     def __init__(self, device_manager):
#         super().__init__()
#         self.device_manager = device_manager
#         self._stop = False

#     def run(self):
#         while not self._stop:
#             self.cycle()

#     def cycle(self):
#         order = self.device_manager.orders.get()
#         if order is None:
#             self._stop = True
#         else:
#             client, method, args, kwargs = order
#             with client.lock:
#                 try:
#                     answer = method(*args, **kwargs)
#                 except Exception as e:
#                     answer = e
#                 client.answer.put(answer)
