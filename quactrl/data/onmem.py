from threading import Lock
from quactrl.data.sqlite import TestSaver


class Session:
    def commit(self):
        if self.db.testsaver:
            for test in self.db.tests:
                self.db.testsaver.save(test)

    def rollback(self):
        pass


class Db:
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

    def __init__(self, connectionstring=None):
        "docstring"
        self.testsaver = None
        if stringconnection:
            pars = stringconnection.split(';')
            filename = pars.pop(0)
            parameters = {}
            for par in pars:
                parameter = par.split('=')
                if len(parameter) == 1:
                    parameters[parameter[0]] = True
                else:
                    parameter[parameter[0]] = parameter[1]

            createschema = parameters.get('createschema', False)
            keepdata = parameters.get('keepdata', False)

            self.testsaver = TestSaver(filename, createschema,
                                        keepdata)

    @property
    def Session(self):
        Session.db = self
        return Session


class Repository:
    def init(self, session):
        self.session = session


class KeyRepo:
    def init(self, session, repodict):
        self.session = session
        self.repodict = repodict

    def add(self, obj):
        with self.session.db.lock:
            self.repodict[obj.key] = obj

    def get(self, key):
        return self.repodict[key]


class RequirementRepo(KeyRepo):
    def init(self, session):
        super().init(session, session.db.requirements)


class RoleRepo(KeyRepo):
    def init(self, session):
        super().init(session, session.db.roles)


class LocationRepo(KeyRepo):
    def init(self, session):
        super().init(session, session.db.locations)


class PersonRepo(KeyRepo):
    def init(self, session):
        super().init(session, session.db.persons)


class ModeRepo(KeyRepo):
    def init(self, session):
        super().init(session, session.db.modes)


class CharacteristicRepo(KeyRepo):
    def init(self, session):
        super().init(session, session.db.characteristics)


class ElementRepo(KeyRepo):
    def init(self, session):
        super().init(session, session.db.elements)


class AttributeRepo(KeyRepo):
    def init(self, session):
        super().init(session, session.db.attributes)


class PartModelRepo(KeyRepo):
    def init(self, session):
        super().init(session, session.db.partmodels)


class PartGroupRepo(KeyRepo):
    def init(self, session):
        super().init(session, session.db.partgroups)


class DeviceModelRepo(KeyRepo):
    def init(self, session):
        super().init(session, session.db.devicemodels)


class DeviceRepo(Repository):
    def add(self, device):
        with self.session.db.lock:
            key = device.location.key
            if key not in self.session.devices:
                self.session.db.devices[key] = []
            self.session.db.devices[key].append(device)

    def getallfrom(self, locationkey):
        return  self.session.db.devices[locationkey]


class PartRepo(Repository):
    def add(self, part):
        with self.session.db.lock:
            if part.model not in self.session.db.parts:
                self.session.db.parts[part.model] = []
            self.session.db.parts[part.model].append(part)

    def getby(self, partmodel, serialnumber):
        if partmodel not in self.session.db.parts:
            return

        parts = self.session.db.parts[partmodel]
        for part in parts:
            if part.tracking == serialnumber:
                return part

    def getlastserialnumber(self, partmodel, batchnumber, pos):
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

        with self.session.db.lock:
            for resource in resources:
                self.session.db.controlplans[(resource, location)] = controlplan

    def getby(self, partmodel, location):
        """Return control plan for a partmodel on a location
        """
        key = (partmodel.key, location.key)
        if key in self.session.db.controlplans:
            return self.session.db.controlplans[key]

        #If there is no controlplan for specific partmodel...
        for group in partmodel.partgroups:
            key = (group.key, location.key)
            if key in self.session.db.controlplans.keys():
                return self.session.db.controlplans[key]


class TestRepo(Repository):
    def add(self, test):
        with self.session.db.lock:
            self.session.db.tests.append(test)
