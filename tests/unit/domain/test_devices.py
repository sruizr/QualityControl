from unittest.mock import patch, Mock
from quactrl.domain.devices import DeviceContainer


class FakeDevice:
    def __init__(self, par_1, par_2, ):
        self.part_1 = part_1
        self.part_2 = part_2


class OtherFakeDevice:
    def __init__(self, par_1):
        self.part_1




class A_DeviceContainer:


    @patch('quactrl.domain.devices.import_class')
    def should_inject_devices_from_dict(self, import_mock):

        devices = {
            'a_device': {'par_1': 'lorem', 'par_2': '>other_device'},
            'other_device': {'par_1': 'ipsum'}
        }
        dev_def_repo = Mock()
        dev_def_repo.find_all_device_names.return_value = devices.keys()
        dev_def_repo.find_by_name.side_effect = lambda name: devices[name]

        container = DeviceContainer(dev_def_repo)

        location = Mock()
        container.set_location(location)
        assert container.location == location
        assert dev_def_repo.set_location.assert_called_with()
