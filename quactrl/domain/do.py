from sqlalchemy.orm import synonym
from quactrl.domain.erp import Item, Resource, Node
from quactrl.domain.plan import PartModel, Process
# from quactrl.domain import dal, Base
# from quactrl.domain.base import Resource, Model
import pdb


class Material(Item):
    __mapper_args__ = {'polymorphic_identity': 'material'}


class Defect(Item):
    __mapper_args__ = {'polymorphic_identity': 'defect'}

    def __init__(self, part, check, failure_mode):
        self.resource = failure_mode
        part.add_defect(self)


class Person(Node):
    __mapper_args__ = {'polymorphic_identity': 'person'}


class Location(Node):
    __mapper_args__ = {'polymorphic_identity': 'location'}


class Device(Resource):
    __mapper_args__ = {'polymorphic_identity': 'device'}


class DeviceRepository:

    def __init__(self, dal):
        self.dal = dal
        self._devices = {}

    def get(self, key):
        if key not in self._devices.keys():
            self.load(key)

        return self._devices[key]

    def load(self, key):
        device_model = self.dal.get_device_model(key)

        full_class_name = device_model.role
        Device = _get_class(full_class_name)

        device = Device(device_model)
        self._devices[key] = device

        if 'components' in device_model.pars.keys():
            for key, value in device_model.pars['components'].items():
                if type(value) is list:
                    device_value = []
                    for v in value:
                        device_value.append(self.get(v))
                else:
                    device_value = self.get(value)

                setattr(device, key, device_value)


class DataAccessModule:
    def __init__(self, dal):
        self.dal = dal
        self._devices = {}
        self._duts = {}

    def get_device(self, data):
        """Return a fully functional device for operating"""

        item_device  = sessdata
        item.model = self._get_model(data['partnumber'])
        item.serial_number = None
        item.tracking = data['batch_number']
        item.batch = get_or_create_batch(data['batch_number'], data['part_number'])
        pass

    def get_or_create_dut(self, **kwargs):
        """Return a fully functional dut for testing"""
        pass

    def get_operator(self, key):
        """Get operator from data layer if not exist it return None"""
        session = self.dal.Session()
        return session.query(Person).filter_by(key=key).first()

    def get_process(self, part_number):
        """Return process by key, None if not exist"""
        session = self.dal.Session()

        return session.query(Process).filter(
            Process.resource_links.any(key=part_number)
            ).filter(
                Process.method_name == 'final_test'
            ).first()
