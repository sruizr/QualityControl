from datetime import datetime
import json
from sqlalchemy import create_engine, ForeignKey, Column, UniqueConstraint
from sqlalchemy.types import (
    String, Integer, DateTime
    )
from sqlalchemy.orm import sessionmaker, backref, relationship
from quactrl.entities import Base
import importlib
import pdb


class Model(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

    # def __repr__(self):
    #     identification = '#{} - '.format(self.id)
    #     return identification + str(self)


class Resource(Model):
    __tablename__ = 'resource'
    key = Column(String)
    is_a = Column(String)
    name = Column(String)
    role = Column(String)
    description = Column(String)
    pars = Column(String)
    __mapper_args__ = {
        'polymorphic_identity': 'resource',
        'polymorphic_on': is_a
    }


class Node(Resource):
    __mapper_args__ = {
        'polymorphic_identity': 'node'
    }


class Item(Model):
    __tablename__ = 'item'
    resource_id = Column(ForeignKey('resource.id'))
    resource = relationship("Resource")
    tracking = Column(String)
    qty = Column(Integer)


# class Movement(Model):
#     __tablename__ = 'movement'
#     item_id = Column(ForeignKey('item.id'))
#     from_node_id = Column(ForeignKey('resource.id'))
#     to_node_id = Column(ForeignKey('resource.id'))
#     input_on = Column(DateTime, default=datetime.now)
#     output_on = Column(DateTime)
#     from_node = relationship()
#     to_node = relationship()
#     item = relationship()


def _get_class(full_class_name):
    packages = full_class_name.split('.')
    if packages[0] == '':
        packages[0] = 'functional_checker.devices'

    class_name = packages.pop()

    module = importlib.import_module('.'.join(packages))

    return getattr(module, class_name)


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
