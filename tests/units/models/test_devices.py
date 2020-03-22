from unittest.mock import patch, Mock
import quactrl.models.devices as devs



class FakeDevice:
    def __init__(self, par_1, par_2, **kwargs):
        self.par_1 = par_1
        self.par_2 = par_2
        for key, value in kwargs.items():
            setattr(self, key, value)


class OtherFakeDevice:
    def __init__(self, par_1):
        self.par_1 = par_1


class A_DeviceProvider:
    def should_produces_singleton_devices(self):
        Device = Mock()
        Device.side_effect = [Mock(), Mock()]

        device_provider = devs.DeviceProvider(Device, 'tracking_content', 1, foo=3)

        device = device_provider()
        other_dev = device_provider()

        assert device is other_dev
        assert device.tracking == 'tracking_content'
        Device.assert_called_with(1, foo=3)


class A_Toolbox:


# class A_DeviceContainer:
#     def setup_dependencies(self, get_class):
#         classes = {'FakeDevice': FakeDevice, 'OtherFakeDevice': OtherFakeDevice}
#         get_class.side_effect = lambda class_name: classes[class_name]

#         self.devices = {
#             'a_device': {
#                 '_strategy': 'factory', 'class': 'FakeDevice',
#                 '_args': ['lorem', '>other_device'],
#                 'par_3': 'ipsum', 'par_4': '>other_device'},
#             'other_device': {'class': 'OtherFakeDevice',
#                              'par_1': 'dolor'}
#         }

#     @patch('quactrl.models.devices.get_class')
#     def should_inject_devices_from_repository(self, get_class):
#         self.setup_dependencies(get_class)

#         container = DeviceContainer(self.devices)

#         # Correct injection of attributes
#         assert container.a_device()
#         assert container.a_device().par_1 == 'lorem'
#         assert container.a_device().par_2 == container.other_device()
#         assert container.a_device().par_3 == 'ipsum'
#         assert container.a_device().par_4 == container.other_device()

#         assert container.other_device() == container.other_device()
#         assert container.other_device().par_1 == 'dolor'

#         # Correct injection of classes
#         assert type(container.a_device()) is FakeDevice
#         assert type(container.other_device()) is OtherFakeDevice
#         assert type(container.a_device().par_2) is OtherFakeDevice
