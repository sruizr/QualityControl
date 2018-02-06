import importlib
import json
import os
from sqlalchemy.orm import synonym, reconstructor, aliased
from quactrl.domain.erp import Item, Resource, Node, NodeRelation, Pars, Flow, Token
from quactrl.domain.plan import PartModel, Operation, DeviceModel
from quactrl.domain import get_component
from quactrl.domain.erp import Path


class Material(Item):
    __mapper_args__ = {'polymorphic_identity': 'material'}


class Person(Node):
    __mapper_args__ = {'polymorphic_identity': 'person'}

    def __init__(self, key, name=''):
        self.key = key
        self.name = name


class Part(Item):
    __mapper_args__ = {'polymorphic_identity': 'part'}

    def __init__(self, part_model, **kwargs):
        Item.__init__(self, resource=part_model, **kwargs)
        self.behaviour = self.resource.get_behaviour()

class Group(Node):
    __mapper_args__ = {'polymorphic_identity': 'group'}


    def add_person(self, *persons):
        for person in persons:
            NodeRelation(self, person)

    def get_persons(self):
        persons = []
        for destination in self.destinations:
            if (destination.relation_class == 'contains' and
                    type(destination.to_node) is Person):
                persons.append(self.destinations.to_node)
        return persons



class Location(Node):
    __mapper_args__ = {'polymorphic_identity': 'location'}

    def __init__(self, key, name=''):
        self.key = key
        self.name = name

    def add_devices(self, *devices):
        for device in devices:
            if device.is_a == 'device':
                pass


class Device(Item):
    __mapper_args__ = {'polymorphic_identity': 'device'}

    def __init__(self, device_model, tracking, pars=None):
        Item.__init__(self, device_model, tracking, )

        if pars:
            self.pars = Pars(pars)

        self.behaviour = None

    def setup(self):
        if not self.resource.pars:
            return None # No class to load

        resource_pars = self.resource.pars.get()
        if 'class_name' not in resource_pars:
            return None # No class to load

        class_name = resource_pars['class_name']
        FunctionalDevice = get_component(class_name)
        if not FunctionalDevice:
            raise Exception('class path {} can not be loaded'.format(class_name))

        pars = {}
        if self.pars:
            pars = self.pars.get()
            self.behaviour = FunctionalDevice(**pars)
        else:
            self.behaviour = FunctionalDevice()

    def assembly(self, devices):
        if self.behaviour:
            self.behaviour.assembly(devices)

    @reconstructor
    def after_load(self):
        self.behaviour = None


class DataAccessModule:
    _devices = {}
    _duts = {}

    def __init__(self, dal):
        self.dal = dal
        self._duts = {}
        self.session = None

    # def open_session(self):
    #     self.session = self.dal.Session()

    # def get_item_by_sn(self, serial_number):
    #     if not self.session:
    #         self.open_session()

    # def get_or_create_dut(self, **kwargs):
    #     """Return a fully functional dut for testing"""
    #     pass

    def get_person(self, key, session=None):
        """Get operator from data layer if not exist it return None"""
        session = self.dal.Session() if session is None else session

        return session.query(Person).filter_by(key=key).first()

    def get_avalaible_inputs(self, location_key, item_args, session=None):
        session = self.dal.Session() if session is None else session

        filters = [Token.state == 'avalaible', Node.key == location_key]
        qry = session.query(Token).join(Node).join(Item)

        if 'resource_key' in item_args:
            qry = qry.join(Resource)
            filters.append(Resource.key == item_args['resource_key'])
        if 'tracking' in item_args:
            filters.append(Item.tracking == item_args['tracking'])

        tokens = qry.filter(*filters).all()

        return [(token.item, token.qty) for token in tokens]

    # def create_dut(self, item):
    #     """Returns a fully functional device"""
    #     if item.resource.pars is None:
    #         return item

    #     device_name = item.resource.key
    #     pars = item.resource.pars.get()
    #     if not device_name in self._duts:
    #         class_name = pars['class_name']
    #         modules = class_name.split('.')
    #         module = importlib.import_module('.'.join(modules[:-1]))
    #         Device = getattr(module, modules[-1], None)
    #         self._duts[device_name] = (Device, pars)

    #     Device, pars = self._devices.get(device_name)
    #     return Device(item, pars)

    # def get_location(self, key):
    #     session = self.dal.Session()
    #     return session.query(Location).filter(Location.key == key).one()

    def get_devices_by_location(self, location_key, session=None):
        """Return a dict with all devices of a location"""
        session = self.dal.Session() if session is None else session

        query = session.query(Device).join(Token).join(Node).filter(
            Node.key == location_key,
            Token.state == 'avalaible'
            ).order_by(Device.tracking)

        devices_by_tracking = {}
        devices_by_key = {}

        for device in query.all():
            device.setup()
            tracking = device.tracking
            devices_by_tracking[tracking] = device

            key = device.resource.key
            if key in devices_by_key:
                if type(devices_by_key[key]) is dict:
                    devices_by_key[key][tracking] = device
                else:
                    first_device = devices_by_key[key]
                    devices_by_key[key] = {
                        first_device.tracking: first_device,
                        device.tracking: device
                        }
            else:
                devices_by_key[key] = device

        for device in devices_by_tracking.values():
            device.assembly(devices_by_tracking)

        return devices_by_key

    # def get_item(self, serial_number, resource_key):
    #     return self.dal.session.query(Item).join(Resource).filter(
    #         Dut.tracking == serial_number,
    #         Resource.key == resource_key
    #         ).first()

    # def create_dut(self, resource_key, serial_number):
    #     resource = self.dal.session.query(Resource).filter(
    #         Resource.key == resource_key).first()

    #     return Dut(resource, tracking= serial_number)

     # def get_dut_at_location(self, serial_number, location_key):
     #    qry = self.dal.session.query(Dut).join(Movement).filter(
     #        Dut.tracking == serial_number,
     #        Movement.to_node is None,
     #        Node.key == location_key
     #        )
     #    return qry.first()
