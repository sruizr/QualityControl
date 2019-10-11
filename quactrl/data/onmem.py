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
    partgroups = {}
    controlplans = {}
    devices = {}
    devicemodels = {}
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


class DocuRepo(Repository):
    pass


class DirectoryRepo(Repository):
    pass


class KeyRepo(Repository):
    def __init__(self, data, dict_name):
        super().__init__(data)
        self._repo = getattr(data.Session(), dict_name)

    def add(self, obj):
        with self.session.lock:
            self._repo[obj.key] = obj

    def remove(self, obj):
        with self.session.lock:
            self._repo.pop(obj.key)

    def get(self, key):
        return self._repo[key]


class FormRepo(KeyRepo):
    pass


class RequirementRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, 'requirements')


class RoleRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, 'roles')


class LocationRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, 'locations')


class PersonRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, 'persons')


class ModeRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, 'modes')


class CharacteristicRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, 'characteristics')


class ElementRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, 'elements')


class AttributeRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, 'attributes')


class PartModelRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, 'partmodels')


class PartGroupRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, 'partgroups')


class DeviceModelRepo(KeyRepo):
    def __init__(self, data):
        super().__init__(data, 'devicemodels')


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
        session = self.data.Session()
        with session.lock:
            if part.model not in session.parts:
                session.parts[part.model] = []
            session.parts[part.model].append(part)

    def get_by(self, partmodel, serialnumber):
        if partmodel not in self.session.parts:
            return

        parts = self.session.parts[partmodel]
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

    def get_by(self, partmodel, location):
        """Return control plan for a partmodel on a location
        """
        key = (partmodel.key, location.key)
        session = self.data.Session()
        if key in session.controlplans:
            return self.session.db.controlplans[key]

        #If there is no controlplan for specific partmodel...
        for group in partmodel.groups:
            key = (group.key, location.key)
            if key in self.session.controlplans.keys():
                return self.session.controlplans[key]


class TestRepo(Repository):
    def add(self, test):
        session = self.data.Session()
        with session.lock:
            session.tests.append(test)
