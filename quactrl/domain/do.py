from sqlalchemy.orm import synonym
import importlib
import json
import os
from quactrl.domain.erp import Item, Resource, Node, NodeRelation, Movement
from quactrl.domain.plan import PartModel, Operation, DeviceModel
import pdb


class Material(Item):
    __mapper_args__ = {'polymorphic_identity': 'material'}

class Person(Node):
    __mapper_args__ = {'polymorphic_identity': 'person'}

    def __init__(self, key, description=''):
        self.key = key
        self.description = description


class Group(Node):
    __mapper_args__ = {'polymorphic_identity': 'group'}

    def __init__(self, key, description=''):
        self.key = key
        self.description = description

    def add_person(self, *persons):
        for person in persons:
            NodeRelation(self, person)

    def get_persons(self):
        persons = []
        for destination in self.destinations:
            node = self.destination.to_node
            # TODO

        return persons


class Location(Node):
    __mapper_args__ = {'polymorphic_identity': 'location'}

    def __init__(self, key, description=''):
        self.key = key
        self.description = description

    def add_devices(self, *devices):
        for device in devices:
            if device.is_a == 'device':
                Movement(
                    from_node=self,
                    item=device
                    )


class Device(Item):
    __mapper_args__ = {'polymorphic_identity': 'device'}


class DataAccessModule:
    _devices = {}
    _duts = {}

    def __init__(self, dal):
        self.dal = dal
        self._devices = {}
        self._duts = {}


    def get_or_create_dut(self, **kwargs):
        """Return a fully functional dut for testing"""
        pass

    def get_operator(self, key):
        """Get operator from data layer if not exist it return None"""
        session = self.dal.Session()
        return session.query(Person).filter_by(key=key).first()

    def get_operation(self, part_number):
        """Return process by key, None if not exist"""
        session = self.dal.Session()

        return session.query(Operation).filter(
            Operation.resource_links.any(key=part_number)
            ).filter(
                Operation.method_name == 'final_test'
            ).first()

    def create_dut(self, item):
        """Returns a fully functional device"""
        if item.resource.pars is None:
            return item

        device_name = item.resource.key
        pars = item.resource.pars.get()
        if not device_name in self._duts:
            class_name = pars['class_name']
            modules = class_name.split('.')
            module = importlib.import_module('.'.join(modules[:-1]))
            Device = getattr(module, modules[-1], None)
            self._duts[device_name] = (Device, pars)

        Device, pars = self._devices.get(device_name)
        return Device(item, pars)

    def get_devices_by_location(self, location):
        """Return a dict with all devices of a location"""
        session = self.dal.Session()
        # TODO: Assert query is correct
        device_datas = session.query(Device).inner(Movement).filter(
            Movement.to_node is None, 'Movement.from_node == location'
            ).order_by(tracking).all()

        devices_by_tracking = {}
        devices_by_key = {}

        for device_data in device_datas:
            pars = device_data.pars.get()
            class_name = pars['class_name']
            modules = class_name.split('.')
            module = importlib.import_module('.'.join(modules[:-1]))
            Device = getattr(module, modules[-1], None)
            device = Device(device_data)
            devices_by_tracking[device_data.tracking] = device
            key = device_data.resource.key
            if key in devices_by_key:
                if type(devices_by_key[key]) is list:
                    devices_by_key[key] = [devices_by_key[key]]
                devices_by_key[key].append(device)
            else:
                devices_by_key[key] = device

        # TODO: Interconnect_devices

        return devices_by_key
