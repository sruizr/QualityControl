from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
from quactrl.models.hhrr import Person, Role
from quactrl.models.operations import Operation, Step, Location
from quactrl.models.quality import Mode
from quactrl.models.devices import Device, DeviceModel
from quactrl.models.products import (Requirement, Element, Attribute,
                                     PartModel, PartGroup, Characteristic)


metadata = MetaData()


class Db:
    def __init__(self, connection_string, create_all=False, **kwargs):
        self.engine = create_engine(connection_string, **kwargs)
        metadata.bind = self.engine

        import quactrl.data.sqlalchemy.tables
        if create_all:
            metadata.create_all()

        # load all mappers
        from quactrl.data.sqlalchemy.mappers import load_all_mappers
        load_all_mappers()

    @property
    def Session(self):
        return sessionmaker(bind=self.engine)


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
        return self.session.query(self.RepoClass).filter(self.RepoClass.key==key).one()


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
        pass


class PartRepo(Repository):
    def get_by(self, part_model, serial_number):
        pass

    def get_last_serial_number(self, part_model, batch_number, pos):
        """Retrieve the last serial number from database (if exists...)
        """
        pass

class ControlPlanRepo(Repository):
    def get_by(self, part_model, location):
        """Return control plan for a part_model on a location
        """
        pass

class TestRepo(Repository):
    pass
