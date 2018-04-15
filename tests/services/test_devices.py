from unittest import Mock
from quactrl.services.devices import Device, DeviceManager, DeviceProxy, Worker


class FakeDevice():
    pass


class A_DeviceProxy:
    def should_has_lock_attribute(self):
        pass

    def should_send_execution_to_workers(self):
        pass



class A_DeviceManager:
    def should_init_workers(self):
        pass

    def should_add_devices(self):
        pass

    def should_stop_workers(self):
        pass


class A_Device:
    def should_load_all_attributes(self):
        pass

    def should_assembly_from_list(self):
        pass


class A_Worker:
    def should_execute_device_methods(self):
        pass
