from sqlalchemy import MetaData, create_engine, and_, cast, desc, BigInteger
from sqlalchemy.orm import session_maker
from quactrl.models.core import Token
from quactrl.models.hhrr import Person, Role
from quactrl.models.operations import Operation, Step, Location
from quactrl.models.quality import Mode, ControlPlan
from quactrl.models.devices import Device, DeviceModel
from quactrl.models.products import (Requirement, Element, Attribute,
                                     PartModel, PartGroup, Characteristic, Part)
from quactrl.models.documents import (Form, Directory)
from quactrl.data import Repository
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


metadata = MetaData()


class Db:
    """Database connection... maybe you should change name
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
        metadata.bind = self.engine

        # load all mappers
        from quactrl.data.sqlalchemy.mappers import load_all_mappers
        load_all_mappers()

        self.Session = session_maker(bind=self.engine, autoflush=False)

    def create_schema(self):
        metadata.create_all()

    def drop_all(self):
        metadata.drop_all()


class KeyRepo(Repository):
    def __init__(self, data, Model):
        super().__init__(data)
        self.Model = Model

    def get(self, key):
        resource = self.session.query(self.Model).filter(
            self.Model.key == key
        ).first()
        if resource is None:
            raise KeyError('resource with key "{}" is not found'.format(key))
        return resource


class RequirementRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, Requirement)


class RoleRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, Role)


class LocationRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, Location)


class PersonRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, Person)


class ModeRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, Mode)


class CharacteristicRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, Characteristic)


class ElementRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, Element)


class AttributeRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, Attribute)


class PartModelRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, PartModel)


class DirectoryRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, Directory)


class FormRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, Form)


class PartGroupRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, PartGroup)


class DeviceModelRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, DeviceModel)


class DeviceRepo(Repository):
    def __init__(self, data):
        super().__init__(data)

    def get_all_from(self, location_key):
        """Returns all devices from a location given its key
        """
        location = self.session.query(Location).filter(Location.key == location_key).one()
        logger.info('Location is {}'.format(location.key))
        results = self.session.query(Device, Token).filter(
            Device.id == Token.item_id).filter(
                Token.node == location).all()
        logger.info('Number of devices are: {}'.format(len(results)))
        return [result[0] for result in results]


class PartRepo(Repository):
    def __init__(self, data):
        super().__init__(data)

    def get_by(self, part_model, serial_number):
        return self.session.query(Part).filter(and_(
            Part.serial_number == serial_number,
            Part.model == part_model
            )).first()

    def get_last_serial_number(self, part_model, batch_number, pos):
        """Retrieve the last serial number from database (if exists...)
        """
        batch_pattern = '%{:06d}%'.format(int(batch_number))
        part = self.session.query(Part).filter(Part.serial_number.like(batch_pattern)).order_by(
            desc(cast(Part.serial_number, BigInteger))).first()

        if part:
            return part.serial_number


class ControlPlanRepo(Repository):
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


class TestRepo(Repository):
    pass
