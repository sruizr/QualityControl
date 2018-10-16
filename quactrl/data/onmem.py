from threading import Lock
from quactrl.models.operations import PartModel, Part_Group


class Session:
    _routes = {}
    _persons = {}
    _locations = {}
    _part_models = {}
    _attributes = {}
    _elements = {}
    _failure_modes = {}
    _locations = {}
    _part_groups = {}
    _routes = {}
    _devices = {}

    _tests = []
    lock = Lock()

    def commit(self):
        pass


class Repository:
    def __init__(self, session):
        self.session = session

class KeyRepo:
    def __init__(self, session, repo_dict):
        self.session = session
        self._repo_dict = repo_dict

    def add(self, obj):
        with self.session.lock:
            self._repo_dict[obj.key] = obj

    def get(self, key):
        return self._repo_dict[key]


class LocationRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._locations)


class PersonRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._persons)


class FailureModeRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._failure_modes)


class CharacteristicRepo(Repository):
    def __init__(self, session):
        super().__init__(session, session._characteristics)


class ElementRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._elements)

class AttributeRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._attributes)


class PartModelsRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._part_models)


class DeviceRepo(Repository):
    def add_to_location(self, device, location):
        if location.key not in self.session._devices:
            self.session._devices[location.key] = []

        self.session._devices[location.key].append(device)


class RouteRepo(Repository):
    def add(self, route):
        location = route.from_node
        resources = []

        for resource_map in route.outputs:
            resource = resource_map.resource
            resources.append(resource)
        with self.session.lock:
            for resource in resources:
                self.session._routes[(resource, location)]

    def get_by_part_model_and_location(self, part_model, location):
        key = (part_model, location)
        if key in self.session._routes:
            return self.session._routes[key]

        for group in part_model.groups:
            key = (group, location)
            if key in self.sessionn._routes:
                return self.session._routes[key]


class TestRepo(Repository):
    def add(self, test):
        with self.session.lock:
            self.session._tests.append(test)
