from sqlalchemy import MetaData, create_engine, and_
from sqlalchemy.orm import sessionmaker
from quactrl.models.core import Token
from quactrl.models.hhrr import Person, Role
from quactrl.models.operations import Operation, Step, Location
from quactrl.models.quality import Mode, ControlPlan
from quactrl.models.devices import Device, DeviceModel
from quactrl.models.products import (Requirement, Element, Attribute,
                                     PartModel, PartGroup, Characteristic, Part)
from quactrl.models.documents import (Form, Directory)
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


metadata = MetaData()


class Db:
    def __init__(self, connection_string):
        if connection_string[:6] == 'sqlite':
            connect_args={'check_same_thread': False}
            kwargs = {}
        else:
            connect_args = {}
            kwargs = {'pool_size': 17, 'pool_recycle': 3600}

        self.engine = create_engine(connection_string, connect_args=connect_args,
                                    **kwargs)
        metadata.bind = self.engine

        # load all mappers
        from quactrl.data.sqlalchemy.mappers import load_all_mappers
        load_all_mappers()

    @property
    def Session(self):
        return sessionmaker(bind=self.engine, autoflush=False)

    def create_schema(self):
        metadata.create_all()

    def drop_all(self):
        metadata.drop_all()


class Repository:
    def __init__(self, session):
        self.session = session

    def add(self, obj):
        self.session.add(obj)


class KeyRepo(Repository):
    def __init__(self, session, RepoClass):
        super().__init__(session)
        self.RepoClass = RepoClass

    def get(self, key):
        resource = self.session.query(self.RepoClass).filter(self.RepoClass.key==key).first()
        if resource is None:
            raise KeyError('resource with key "{}" is not found'.format(key))
        return resource

class RequirementRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, Requirement)


class RoleRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, Role)


class LocationRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, Location)


class PersonRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, Person)


class ModeRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, Mode)


class CharacteristicRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, Characteristic)


class ElementRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, Element)


class AttributeRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, Attribute)


class PartModelRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, PartModel)


class DirectoryRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, Directory)


class FormRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, Form)


class PartGroupRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, PartGroup)


class DeviceModelRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, DeviceModel)


class DeviceRepo(Repository):
    def __init__(self, session):
        super().__init__(session)

    def get_all_from(self, location_key):
        location = self.session.query(Location).filter(Location.key == location_key).one()
        logger.info('Location is {}'.format(location.key))
        results =  self.session.query(Device, Token).filter(
            Device.id == Token.item_id).filter(
                Token.node == location).all()
        logger.info('Number of devices are: {}'.format(len(results)))
        return [result[0] for result in results]


class PartRepo(Repository):
    def __init__(self, session):
        super().__init__(session)

    def get_by(self, part_model, serial_number):
        return self.session.query(Part).filter(and_(
            Part.serial_number == serial_number,
            Part.model == part_model
            )).first()

    def get_last_serial_number(self, part_model, batch_number, pos):
        """Retrieve the last serial number from database (if exists...)
        """
        pass


class ControlPlanRepo(Repository):
    def get_by(self, part_model, location):
        """Return control plan for a part_model on a location
        """
        control_plan = self.session.query(ControlPlan).join(ControlPlan.outputs).filter(
            and_(
                ControlPlan.source == location,
                PartModel.key == part_model.key)
            ).first()

        if control_plan is None:
            for group in part_model.groups:
                control_plan = self.session.query(ControlPlan).join(ControlPlan.outputs).filter( and_(
                    ControlPlan.source == location,
                    PartGroup.key == group.key)
                ).first()
                if control_plan:
                    return control_plan

        return control_plan


class TestRepo(Repository):
    pass
