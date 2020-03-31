from sqlalchemy import MetaDal, create_engine, and_, cast, desc, BigInteger
from sqlalchemy.orm import sessionmaker
from quactrl.models.core import Token, Item
from quactrl.models.hhrr import Person, Role
from quactrl.models.operations import Location
from quactrl.models.quality import Mode, ControlPlan, Measurement, Test
from quactrl.models.devices import Device, DeviceModel
from quactrl.models.products import (Requirement, Element, Attribute,
                                     PartModel, PartGroup, Characteristic, Part)
from quactrl.models.documents import (Form, Directory)
import quactrl.dal.repositories as _
import logging


logger = logging.getLogger(__name__)


metadal = MetaDal()


class Dalbase:
    """Dalbase connection layer
    """
    def __init__(self, connection_string):
        if connection_string[:6] == 'sqlite':
            connect_args = {'check_same_thread': False}
            kwargs = {}
        else:
            connect_args = {}
            kwargs = {'pool_size': 17, 'pool_recycle': 3600}

        self.engine = create_engine(connection_string,
                                    connect_args=connect_args,
                                    **kwargs)
        metadal.bind = self.engine

        # load all mappers
        from quactrl.dal.sqlalchemy.mappers import load_all_mappers
        load_all_mappers()

        self.Session = sessionmaker(bind=self.engine, autoflush=False)

    def create_schema(self):
        metadal.create_all()

    def drop_all(self):
        """Drop all tables, be carefull
        """
        metadal.drop_all()


class KeyRepo:
    def __init__(self, data_access_layer, Model):
        """Base class for repository with a key field
        """
        self.dal = data_access_layer
        self.Model = Model

    def get(self, key):
        resource = self.session.query(self.Model).filter(
            self.Model.key == key
        ).first()
        if resource is None:
            raise KeyError('resource with key "{}" is not found'.format(key))
        return resource

    def get_all(self):
        return self.session.query(self.Model).all()


class RequirementRepo(KeyRepo, _.RequirementRepo):
    def __init__(self, dal):
        KeyRepo.__init__(self, dal, Requirement)


class RoleRepo(KeyRepo, _.RoleRepo):
    def __init__(self, dal):
        KeyRepo.__init__(self, dal, Role)


class LocationRepo(KeyRepo, _.LocationRepo):
    def __init__(self, dal):
        KeyRepo.__init__(self, dal, Location)

    def where_is(self, location):
        return self.session.query(Location).filter(
            location in Location.sub_locations
        ).first()


class PersonRepo(KeyRepo, _.PersonRepo):
    def __init__(self, dal):
        KeyRepo.__init__(self, dal, Person)


class ModeRepo(KeyRepo, _.ModeRepo):
    def __init__(self, dal):
        KeyRepo.__init__(self, dal, Mode)


class CharacteristicRepo(KeyRepo, _.CharacteristicRepo):
    def __init__(self, dal):
        KeyRepo.__init__(self, dal, Characteristic)


class ElementRepo(KeyRepo, _.ElementRepo):
    def __init__(self, dal):
        KeyRepo.__init__(self, dal, Element)


class AttributeRepo(KeyRepo, _.AttributeRepo):
    def __init__(self, dal):
        KeyRepo.__init__(self, dal, Attribute)


class PartModelRepo(KeyRepo, _.PartModelRepo):
    def __init__(self, dal):
        KeyRepo.__init__(self, dal, PartModel)


class DirectoryRepo(KeyRepo, _.DirectoryRepo):
    def __init__(self, dal):
        KeyRepo.__init__(self, dal, Directory)


class FormRepo(KeyRepo, _.FormRepo):
    def __init__(self, dal):
        KeyRepo.__init__(self, dal, Form)


class PartGroupRepo(KeyRepo, _.PartGroupRepo):
    def __init__(self, dal):
        KeyRepo.__init__(self, dal, PartGroup)


class DeviceModelRepo(KeyRepo, _.DeviceModelRepo):
    def __init__(self, dal):
        KeyRepo.__init__(self, dal, DeviceModel)


class DeviceRepo(_.DeviceRepo):
    def get_all_from(self, location_key, include_parents=True):
        """Returns all devices from a location given its key
        """
        devices = []
        location_repo = self.dal.location_repo()
        location = location_repo.get(location_key)
        if include_parents:
            parent = location_repo.where_is(location)
            if parent:
                devices.extend(self.get_all_from(parent.key, include_parents))

        results = self.session.query(Device, Token).filter(
            Device.id == Token.item_id).filter(
                Token.node == location).all()

        devices.extend([result[0] for result in results])
        logger.info('Number of devices in {} are: {}'.format(location_key, results))

        return devices


class PartRepo(_.PartRepo):
    def get_by(self, part_model, serial_number):
        return self.session.query(Part).filter(and_(
            Part.serial_number == serial_number,
            Part.model == part_model
            )).first()

    def get_last_serial_number(self, part_model, batch_number, pos):
        """Retrieve the last serial number from database (if exists...)
        """
        batch_pattern = '%{:06d}%'.format(int(batch_number))
        part = self.session.query(Part).filter(
            Part.serial_number.like(batch_pattern)).order_by(
                desc(cast(Part.serial_number, BigInteger))
            ).first()

        if part:
            return part.serial_number


class ControlPlanRepo(_.ControlPlanRepo):
    def get_by(self, part_model, location):
        """Return control plan for a part_model on a location
        """
        control_plan = self.session.query(ControlPlan).join(
            ControlPlan.outputs).filter(
                and_(
                    ControlPlan.source == location,
                    PartModel.key == part_model.key)
            ).first()

        if control_plan is None:
            for group in part_model.groups:
                control_plan = self.session.query(ControlPlan).join(
                    ControlPlan.outputs).filter(and_(
                        ControlPlan.source == location,
                        PartGroup.key == group.key)
                    ).first()
                if control_plan:
                    return control_plan

        return control_plan


class TestRepo(_.TestRepo):
    def get_last(self, location_key, tracking):
        location = self.session.query(Location).filter(
            Location.key == location_key
        ).first()

        tests = self.session.query(Test).join(ControlPlan).join(Token).join(Item).filter(
            ControlPlan.source == location,
            Item.tracking == tracking
        ).order_by(Test.id.desc()).first()
        return tests

    def get_samples(self, test):
        samples = self.session.query(Part).join(Token).filter(
            Token.flow == test
        ).all()
        return list(samples)


class MeasurementRepo(_.MeasurementRepo):
    def get_all(self, check):
        measurements = self.session.query(Measurement).join(Token).filter(
            Token.flow == check
        ).all()
        return measurements
