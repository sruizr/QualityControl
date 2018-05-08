from unittest.mock import Mock
from tests import TestWithPatches
from quactrl.managers.devices import DeviceManager, DeviceProxy
import time
import threading


class A_Device:
    pass


class A_DeviceManager(TestWithPatches):
    def setup_method(self, method):
        patchers = [
            'quactrl.managers.devices.dal',
            'quactrl.managers.devices.DeviceProxy',
            'quactrl.managers.devices.get_class'
        ]
        self.create_patches(patchers)
        self.dev_manager = DeviceManager()

    def gen_domain_devices(self):
        dev_models = [
            Mock(**{
                'key': 'dev_key_{}'.format(i),
                'name': 'dev_name_{}'.format(i),
                'pars': {
                    'type': 'class.Dev{}'.format(i)
                }

            })
            for i in range(3)
        ]

        devices = [
            Mock(**{
                'tracking': '00{}'.format(i),
                'pars': {
                    'parameter': i
                }
            })
            for i in range(5)
        ]

        devices[0].resource = devices[1].resource = dev_models[0]
        devices[2].resource = devices[3].resource = dev_models[1]
        devices[4].resource = dev_models[2]

        return devices

    def should_behave_like_dict(self):
        devices = {'name1': Mock(),
                   'name2': Mock()}
        self.dev_manager.devices = devices

        assert devices['name1'] == self.dev_manager['name1']
        new_device = Mock()
        self.dev_manager['other'] = new_device
        assert self.dev_manager['other'] == new_device


    def should_load_devs_from_location(self):
        devices = self.gen_domain_devices()
        self.dal.get_devices_by.return_value = devices
        self.DeviceProxy.side_effect = [Mock(name=device.resource.name,
                                            tracking=device.tracking)
                                        for device in devices]
        self.dev_manager.create_device = Mock()
        self.dev_manager.load_devs_from('location_key')

        self.dal.get_devices_by.assert_called_with(location_key='location_key')
        assert len(self.dev_manager.devices) == 3

    def should_create_device_proxies(self):

        self.dev_manager = DeviceManager()
        pars = {
            'class_name': 'ClassName',
            'parameter': 1
        }
        Device = self.get_class.return_value

        self.dev_manager.create_device(pars)

        Device.assert_called_with(parameter=1)
        self.DeviceProxy.assert_called_with(
            Device.return_value, self.dev_manager
        )


class A_DeviceProxy:

    def should_lock_device_when_executed(self):
        wait = 0.1

        class FakeDevice:
            def method(self):
                time.sleep(wait)

        class DevClient(threading.Thread):
            def __init__(self, device):
                super().__init__()
                self.device = device

            def run(self):
                self.device.method()

        fake_device = FakeDevice()
        manager = Mock()

        device_proxy = DeviceProxy(fake_device, manager)
        client = DevClient(device_proxy)
        client.start()

        assert not device_proxy.lock.acquire(timeout=0)
        assert device_proxy.lock.acquire(timeout=wait+0.2)

        device_proxy.lock.release()
