from unittest.mock import Mock, patch
import quactrl.entities.base as base
from quactrl.entities import DataAccessLayer
import pytest
import pdb

current = pytest.mark.current


@patch('quactrl.entities.base.importlib')
def test_get_class(mock_importlib):
    full_class_name = 'module.submodule.MyClass'

    Device = base._get_class(full_class_name)

    mock_importlib.import_module.assert_called_with('module.submodule')
    assert Device == mock_importlib.import_module.return_value.MyClass


class A_DataAccessLayer:

    def should_have_a_test(self):
        dal = DataAccessLayer()
        dal.db_init('sqlite:///:memory:', True)
        dal.prepare_db()

        session = dal.Session()

        node = base.Node()
        node.description = 'description'
        node.key = 'key'
        node.name = 'name'
        node.parameters = '{"test": 1}'
        node.role = 'quactrl.Class'

        session.add(node)

        assert node.id is None
        session.commit()

        assert node.id is not None
        assert node.is_a == 'node'


class A_DeviceRepository:

    def setup_method(self, method):
        self.patcher = patch('quactrl.entities.base._get_class')
        self.get_class = self.patcher.start()

    def tear_down(self, method):
        self.patcher.stop()

    def should_get_device_by_key(self):
        dal = Mock(name='dal')
        device_model_mock = dal.get_device_model.return_value
        device_model_mock.role = 'module.Class'
        device_model_mock.pars = {}

        device_repo = base.DeviceRepository(dal)

        key = 'key'
        device = device_repo.get(key)

        dal.get_device_model.assert_called_with(key)
        self.get_class.assert_called_with('module.Class')
        assert device == self.get_class().return_value

    def should_load_device_with_components(self):
        dal = Mock(name='dal')
        device_model = dal.get_device_model.return_value
        device_model.pars = {
            'components': {
                'test': ['key1', 'key2'],
                'test_simple': 'key3'
                }
            }

        device_repo = base.DeviceRepository(dal)

        key = 'key'
        device_repo.load(key)
        device = device_repo.get(key)

        assert len(device.test) == 2
        assert hasattr(device, 'test_simple')
