import types
from threading import Lock
from quactrl.helpers import get_class
from quactrl.domain.persistence import dal
import quactrl.domain.queries as qry


class DeviceManager:
    """Management of a device repository with locking capabilities """
    def __init__(self):
        self.devices = {}
        self.lock = Lock()

    def __getitem__(self, key):
        return self.devices[key]

    def __setitem__(self, name, device):
        device.name = name
        if name in self.devices.keys():
            if type(self.devices[name]) is not dict:
                first_dev = self.devices[name]
                self.devices[name] = {first_dev.tracking: first_dev}
            self.devices[name][device.tracking] = device
        else:
            self.devices[name] = device

    def __delitem__(self, key):
        del self.devices[key]

    def load_devs_from(self, location_key):
        """Load devices into manager from a location"""
        devices = qry.get_devices_by(location_key=location_key)

        # Load proxies
        dev_proxies = []
        for dev in devices:
            try:
                dev_proxy = DeviceProxy(dev.resource.name, dev.tracking, dev.config_pars)
            except Exception:
                dev_proxy = None
            dev_proxies.append(dev_proxy)

        # for dev_proxy in dev_proxies:
        for dev_proxy in dev_proxies:
            if dev_proxy:
                self.devices[dev_proxy.name] = dev_proxy

    def assembly_all(self):
        devices_by_tracking = {}
        for device in self.devices.values():
            if type(device) is dict:
                for _device in device.values():
                    devices_by_tracking[_device.tracking] = _device
            else:
                devices_by_tracking[device.tracking] = device

        for device in devices_by_tracking.values():
            device.assembly(devices_by_tracking)


class DeviceProxy:
    """Proxy with thread safe calls of devices"""
    def __init__(self, name, tracking, dev_pars):
        self.lock = Lock()  # Thread safe of DeviceProxy calls
        self._implementation = self._create_device(dev_pars)
        self.tracking = tracking
        self.name = name

    def _create_device(self, pars):
        class_name = pars.pop('class_name')

        Device = get_class(class_name)
        return Device(**pars)

    def __getattr__(self, name):
        if hasattr(self._implementation, name):
            self._method = getattr(self._implementation, name)
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

    def is_bussy(self):
        bussy = not self.lock.acquire(timeout=0)
        if not bussy:
            self.lock.release()
        return bussy



device_manager = DeviceManager()  # Singleton !
