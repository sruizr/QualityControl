from threading import Lock
import sqlite3


class Session:
    _routes = {}
    _persons = {}
    _locations = {}
    _part_models = {}
    _attributes = {}
    _elements = {}
    _modes = {}
    _locations = {}
    _part_groups = {}
    _routes = {}
    _devices = {}
    _device_models = {}
    _tests = []
    _roles = {}
    _parts = {}
    _requirements = {}
    _characteristics = {}
    lock = Lock()

    def __init__(self, out_path):
        pass
        # self._tests_f = open(os.path.join(out_path, "tests.csv"), 'a')
        # self._checks_f = open(os.path.join(out_path, "checkss.csv"), 'a')
        # self._measures_f = open(os.path.join(out_path, "measures.csv"), 'a')
        # self._defects_f = open(os.path.join(out_path, "defects.csv"), 'a')

    def commit(self):
        pass
        # self._tests_f.flush()
        # self._checks_f.flush()
        # self._measures_f.flush()
        # self._defects_f.flush()


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


class RequirementRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._requirements)


class RoleRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._roles)


class LocationRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._locations)


class PersonRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._persons)


class ModeRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._modes)


class CharacteristicRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._characteristics)


class ElementRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._elements)


class AttributeRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._attributes)


class PartModelRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._part_models)


class DeviceModelRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._device_models)


class DeviceRepo(Repository):
    def add(self, device):
        with self.session.lock:
            key = device.location.key
            if key not in self.session._devices:
                self.session._devices[key] = []
            self.session._devices[key].append(device)

    def get_all_from(self, location_key):
        devices = {}
        all_devices = self.session._devices[location_key]
        for device in all_devices:
            devices[device.name] = device
        return devices


class PartRepo(Repository):
    def add(self, part):
        with self.session.lock:
            if part.model not in self.session.parts:
                self.session._parts[part.model] = []
            self.session._parts[part.model].append(part)

    def get(self, part_model, serial_number):
        if part_model not in self.session._parts:
            return

        parts = self.session._parts[part_model]
        for part in parts:
            if part.tracking == serial_number:
                return part

    def get_last_serial_number(self, part_model, sn_filter):
        for parts in self.session._parts.values():
            pass


class RouteRepo(Repository):
    def add(self, route):
        location = route.source.key
        resources = []

        for resource_map in route.outputs:
            key = resource_map.key
            resources.append(key)

        with self.session.lock:
            for resource in resources:
                self.session._routes[(resource, location)] = route

    def get_by_part_model_and_location(self, part_model, location):
        key = (part_model.key, location.key)
        if key in self.session._routes:
            return self.session._routes[key]

        for group in part_model.part_groups:
            key = (group, location)
            if key in self.sessionn._routes:
                return self.session._routes[key]


class TestRepo(Repository):
    def add(self, test):
        with self.session.lock:
            self.session._tests.append(test)
