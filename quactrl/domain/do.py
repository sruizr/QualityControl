from quactrl.domain.base import (
    Column, ForeignKey, relationship,
    Integer, String, DateTime
)
from quactrl.domain import dal, Base
from quactrl.domain.base import Resource, Model
import pdb


class Batch:
    def __init__(self, part_number, batch_number, operator):
        self.part_number = part_number
        self.batch_number = batch_number
        self.operator = operator
        self.close_date = None
        self.items = {}


class Item:

    def __init__(self, serial_number, batch, part):
        self.batch = batch
        self.part = part
        self.sn = serial_number
        self.status = None
        self.tests = []

    def validate(self, serial_number):
        pass

    @classmethod
    def has_passed_test(self, serial_number):
        return False


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
    __tablename__ = 'elements'
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
