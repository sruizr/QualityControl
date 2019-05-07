from threading import Lock
from quactrl.data import Repository


class Session:
    routes = {}
    persons = {}
    locations = {}
    partmodels = {}
    attributes = {}
    elements = {}
    modes = {}
    locations = {}
    partGroups = {}
    controlplans = {}
    devices = {}
    dDeviceModels = {}
    tests = []
    roles = {}
    parts = {}
    requirements = {}
    characteristics = {}
    lock = Lock()

    def commit(self):
        pass

    def rollback(self):
        """It doesn't work...
        """
        pass


class Db:
    def __init__(self, *args, **kwargs):
        pass

    @property
    def Session(self):
        """Session class with thread locking capabilities
        """
        return Session


class KeyRepo(Repository):
    def init(self, data, dict_name):
        super().__init__(data)
        self._repo = getattr(data.Session, dict_name)

    def add(self, obj):
        with self.session.lock:
            self._repo[obj.key] = obj

    def remove(self, obj):
        with self.session.lock:
            self._repo.pop(obj.key)

    def get(self, key):
        return self._repo[key]


class RequirementRepo(KeyRepo):
    def init(self, data):
        super().init(data, 'requirements')


class RoleRepo(KeyRepo):
    def init(self, data):
        super().init(data, 'roles')


class LocationRepo(KeyRepo):
    def init(self, data):
        super().init(data, 'locations')


class PersonRepo(KeyRepo):
    def init(self, data):
        super().init(data, 'persons')


class ModeRepo(KeyRepo):
    def init(self, data):
        super().init(data, 'modes')


class CharacteristicRepo(KeyRepo):
    def init(self, data):
        super().init(data, 'characteristics')


class ElementRepo(KeyRepo):
    def init(self, data):
        super().init(data, 'elements')


class AttributeRepo(KeyRepo):
    def init(self, data):
        super().init(data, 'attributes')


class PartModelRepo(KeyRepo):
    def init(self, data):
        super().init(data, 'partmodels')


class PartGroupRepo(KeyRepo):
    def init(self, data):
        super().init(data, 'partgroups')


class DeviceModelRepo(KeyRepo):
    def init(self, data):
        super().init(data, 'devicemodels')


class DeviceRepo(Repository):
    def add(self, device):
        session = self.data.Session()
        with session.lock:
            key = device.location.key
            if key not in self.session.devices:
                session.devices[key] = []
            session.devices[key].append(device)

    def get_all_from(self, locationkey):
        return self.data.Session().devices[locationkey]


class PartRepo(Repository):
    def add(self, part):
        session = self.data.Sesssion()
        with session.lock:
            if part.model not in session.parts:
                session.parts[part.model] = []
            session.parts[part.model].append(part)

    def get(self, partmodel, serialnumber):
        if partmodel not in self.session.db.parts:
            return

        parts = self.session.db.parts[partmodel]
        for part in parts:
            if part.tracking == serialnumber:
                return part

    def get_last_serialnumber(self, partmodel, batchnumber, pos):
        """Retrieve the last serial number from database (if exists...)
        """
        if hasattr(self.session.db, 'testsaver'):
            return self.session.db.testsaver.getmaxpartsn(partmodel, batchnumber, pos)


class ControlPlanRepo(Repository):
    def add(self, controlplan):
        location = controlplan.source.key
        resources = []

        for resourcemap in controlplan.outputs:
            key = resourcemap.key
            resources.append(key)

        session = self.data.Session()
        with session.lock:
            for resource in resources:
                session.controlplans[(resource, location)] = controlplan

    def get(self, partmodel, location):
        """Return control plan for a partmodel on a location
        """
        key = (partmodel.key, location.key)
        session = self.data.Session()
        if key in session.controlplans:
            return self.session.db.controlplans[key]

        #If there is no controlplan for specific partmodel...
        for group in partmodel.partgroups:
            key = (group.key, location.key)
            if key in self.session.db.controlplans.keys():
                return self.session.db.controlplans[key]


class TestRepo(Repository):
    def add(self, test):
        session = self.data.Session()
        with session.lock:
            session.tests.append(test)
