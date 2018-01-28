from quactrl.domain.base import (
    Column, ForeignKey, relationship,
    Integer, String, DateTime
)
from sqlalchemy.orm import synonym
from quactrl.domain.erp import Item, Resource, Node
from quactrl.domain.plan import PartModel, Process,
from quactrl.domain import dal, Base
from quactrl.domain.base import Resource, Model
import pdb


class Material(Item):
    __mapped_args__ = {'polymorphic_identity': 'material'}


class Defect(Item):
    __mapper_args__ = {'polymorphic_identity': 'defect'}
    def __init__(self, part, check, failure_mode):
        self.resource = failure_mode
        part.add_defect(self)


class Device:
    pass


class Dut(Device):
    pass


class Person(Node):
    __mapper_args__ = {'polymorphic_identity': 'person'}



class Location(Node):
    __mapper_args__ = {'polymorphic_identity': 'location'}



class Batch:
    def __init__(self, part_number, batch_number, operator):
        self.part_number = part_number
        self.batch_number = batch_number
        self.operator = operator
        self.close_date = None
        self.items = {}


class ElementComposition(Base):
    __tablename__ = 'element_compositions'

    parent_id = Column(Integer, ForeignKey('elements.id'), primary_key=True)
    parent = relationship("Element", back_populates="composed_by",
                          foreign_keys=[parent_id])

    child_id = Column(Integer, ForeignKey('elements.id'), primary_key=True)
    child = relationship("Element", back_populates="used_by",
                         foreign_keys=[child_id])

    qty = Column(Integer)

    def __init__(self, parent, child, qty=1):
        self.parent = parent
        self.child = child
        self.qty = qty


class Element(Model):
    name = Column(String(50))
    key = Column(String(15))
    composed_by = relationship('ElementComposition',back_populates='parent',
                               foreign_keys='ElementComposition.parent_id')
    used_by = relationship('ElementComposition', back_populates='child',
                           foreign_keys='ElementComposition.child_id')

    def __init__(self, name, key=None):
        self.name = name
        self.key = key

    def __str__(self):
        description = self.name
        key_description = '[]'
        if self.key:
            key_description = '[{}]'.format(self.key)

        return self.name + key_description

    def __repr__(self):
        identification = '#{} - '.format(self.id)
        return identification + str(self)


class Operation(Model):
    __tablename__ = 'operations'
    key = Column(String(15))
    name = Column(String(150))
    responsible = Column(String(50))
    device_list = None

    def __init__(self, key, responsible, name=None):
        self.key = key
        self.responsible = responsible
        self.name = name


class Device(Resource):
    __mapper_args__ = {
        'polymorphic_identity': 'resource'
        }


class DeviceBase:
    def __init__(self, model):
        self.model = model


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

    def  get_or_create_batch(self, key, partnumber):
        """Get or create batch """
        pass

    def get_or_create_item_device(self, data):
        """Return a fully functional item"""
        item.model = self._get_model(data['partnumber'])
        item.serial_number = None
        item.tracking = data['batch_number']
        item.batch = get_or_create_batch(data['batch_number'], data['part_number'])
        pass

    def get_operator(self, data):
        """Get operator from data layer if not exist it return None"""
        pass

    def get_process(pass, key):
        """Return process by key, None if not exist"""
        pass

    def get_test_plan(self, process, partnumber=None):
        """Return test plan for process and partnumber"""
        pass

    def get_device(self, key):
        """Return a fully functional device"""
        pass

    def get_model(self, partnumber):
        pass
