from threading import Lock
from quactrl.data.sqlite import TestSaver


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
    _control_plans = {}
    _devices = {}
    _device_models = {}
    _tests = []
    _roles = {}
    _parts = {}
    _requirements = {}
    _characteristics = {}
    lock = Lock()

    def __init__(self, string_connection):
        """
        """
        self.test_saver = None
        if string_connection:
            pars = string_connection.split(';')
            file_name = pars.pop(0)
            parameters = {}
            for par in pars:
                parameter = par.split('=')
                if len(parameter) == 1:
                    parameters[parameter[0]] = True
                else:
                    parameter[parameter[0]] = parameter[1]

            create_schema = parameters.get('create_schema', False)
            keep_data = parameters.get('keep_data', False)

            self.test_saver = TestSaver(file_name, create_schema,
                                        keep_data)

    def commit(self):
        if self.test_saver:
            for test in self._tests:
                if not hasattr(test, '_id'):
                    self.test_saver.save(test)

    def rollback(self):
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


class PartGroupRepo(KeyRepo):
    def __init__(self, session):
        super().__init__(session, session._part_groups)


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
        return  self.session._devices[location_key]


class PartRepo(Repository):
    def add(self, part):
        with self.session.lock:
            if part.model not in self.session.parts:
                self.session._parts[part.model] = []
            self.session._parts[part.model].append(part)

    def get_by(self, part_model, serial_number):
        if part_model not in self.session._parts:
            return

        parts = self.session._parts[part_model]
        for part in parts:
            if part.tracking == serial_number:
                return part

    def get_last_serial_number(self, part_model, batch_number, pos):
        if hasattr(self, 't'):
            return self.test_saver.get_max_part_sn(part_model, batch_number, pos)


class ControlPlanRepo(Repository):
    def add(self, control_plan):
        location = control_plan.source.key
        resources = []

        for resource_map in control_plan.outputs:
            key = resource_map.key
            resources.append(key)

        with self.session.lock:
            for resource in resources:
                self.session._control_plans[(resource, location)] = control_plan

    def get_by(self, part_model, location):
        """Return control plan for a part_model on a location
        """
        key = (part_model.key, location.key)
        print(key)
        if key in self.session._control_plans:
            return self.session._control_plans[key]

        #If there is no control_plan for specific part_model...
        for group in part_model.part_groups:
            key = (group.key, location.key)
            if key in self.session._control_plans.keys():
                return self.session._control_plans[key]


class TestRepo(Repository):
    def add(self, test):
        with self.session.lock:
            self.session._tests.append(test)
