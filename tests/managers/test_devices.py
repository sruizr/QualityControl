from unittest.mock import Mock
from tests import TestWithPatches
from quactrl.managers.devices import DeviceManager, DeviceProxy
import time
import threading
import pytest


class A_DeviceManager(TestWithPatches):
    def setup_method(self, method):
        patchers = [
            'quactrl.managers.devices.dal',
            'quactrl.managers.devices.DeviceProxy',
        ]
        self.create_patches(patchers)
        self.dev_manager = DeviceManager()

    def should_behave_like_dict(self):
        devices = [Mock(tracking=i) for i in range(3)]

        dev_manager = DeviceManager()
        dev_manager['name1'] = devices[0]

        assert dev_manager['name1'] == devices[0]

        dev_manager['name1'] = devices[1]
        assert dev_manager['name1'][0] == devices[0]
        assert dev_manager['name1'][1] == devices[1]

        del dev_manager['name1']
        assert 'name1' not in dev_manager.devices

    def should_load_devs_from_location(self):
        devices = [Mock() for i in range(3)]
        self.dal.get_devices_by.return_value = devices

        device_proxies = []
        for i in range(3):
            device = Mock()
            device.name = i
            device_proxies.append(device)
        self.DeviceProxy.side_effect = device_proxies

        dev_manager = DeviceManager()
        dev_manager.load_devs_from('location_key')

        self.dal.get_devices_by.assert_called_with(location_key='location_key')
        assert len(dev_manager.devices) == 3
        assert dev_manager[0] == device_proxies[0]

    def should_assembly_all_devices(self):
        dev_manager = DeviceManager()
        devices = [Mock(tracking=i) for i in range(4)]
        names = ['name1', 'name1', 'name2', 'name3']
        for device, name in zip(devices, names):
            device.name = name
            dev_manager[name] = device

        dev_manager.assembly_all()

        device_by_track = {i: devices[i] for i in range(4)}
        for device in devices:
            device.assembly.assert_called_with(device_by_track)


class FakeDevice:
    def __init__(self, delay, **pars):
        self.delay = delay

    def fake_method(self):
        time.sleep(self.delay)
        return 'result'


class A_DeviceProxy(TestWithPatches):

    def setup_method(self, method):
        definitions = ['quactrl.managers.devices.get_class']
        self.create_patches(definitions)
        self.device_proxy = DeviceProxy('name', 'tracking', {'class_name': 'fake.Class', 'other_par': 1})

    def should_init_with_device_implementation(self):
        Device = self.get_class.return_value
        device = Device.return_value

        self.get_class.assert_called_with('fake.Class')
        assert self.device_proxy.name == 'name'
        assert self.device_proxy.tracking == 'tracking'
        Device.assert_called_with(other_par=1)
        assert self.device_proxy._implementation == device

    def should_proxy_device_methods(self):
        self.get_class.return_value = FakeDevice

        device_proxy = DeviceProxy('name', 'tracking', {'class_name': 'fake.FakeDevice', 'delay': 0})

        assert device_proxy.fake_method() == 'result'

    def should_lock_itself_when_executed(self):

        class FakeClient(threading.Thread):
            def __init__(self, device):
                super().__init__()
                self.device = device

            def run(self):
                self.device.fake_method()

        delay = 0.5
        self.get_class.return_value = FakeDevice

        device_proxy = DeviceProxy(
            'name', 'tracking',
            {'class_name': 'fake.FakeDevice', 'delay': delay}
        )
        client = FakeClient(device_proxy)
        client.start()

        assert device_proxy.is_bussy()
        time.sleep(delay + 0.2)
        assert not device_proxy.is_bussy()
