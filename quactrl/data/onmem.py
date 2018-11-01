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
        pars = string_connection.split(';')
        output_path = pars.pop(0)
        self.conn = sqlite3.connect(output_path)
        parameters = {}
        for parameter in pars:
            field, value = parameter.split('=')
            parameters[field] = value

        if 'clear' in parameters:
            self._clear_out_data()

    def _clear_out_data(self):
        c = self.conn.cursor()
        c.execute('delete * from Measurements')
        c.execute('delete * from Defects')
        c.execute('delete * from Actions')
        c.execute('delete * from Tests')
        c.execute('delete * from Parts')
        c.commit()

    def commit(self):
        self.c = self.conn.cursor()
        for test in self._tests:
            if not hasattr(test, '_id'):
                part = self._upsert_part(test.inbox['part'])
                self._insert_test(test)
                for action in test.actions:
                    if action.__class__.__name__ == 'Check':
                        check = action
                        self._insert_check(check, test._id)
                        for measurement in check.measurements:
                            self._insert_measurement(measurement, check)
                        for defect in check.defects:
                            self._insert_defect(defect, check)
                    else:
                        self._insert_action(action)

        self.c.commit()

    def _upsert_part(self, part):
        id = self.c.execute(
            'select id from Parts where part_number=?, serial_number=?',
            (part.model.key, part.serial_number)
        )
        if not id:
            self.c.execute(
                'insert into Parts (part_number, serial_number) values (?, ?)',
                (part.model.key, part.serial_number)
            )
            id = self.c.lastrowid

        part._id = id

    def _insert_test(self, test):
        self.c.execute(
            ('insert into Tests '
             '(fk_part, started_on, finished_on, responsible_key, state) '
             'values(?, ?, ?, ?)'),
            (test.part._id, test.started_on, test.finished_on,
             test.state, test.responsible.key)
        )
        test._id = self.c.lastrowid

    def _insert_check(self, check):
        self.c.execute(
            ('insert into Actions ',
             '(fk_test, started_on, finished_on, description, state) '
             'values (?, ?, ?, ?, ?)'),
            (check.test._id, check.started_on, check.finished_on,
             check.requirement.description, check.state)
        )
        check._id = self.c.lastrowid

    def _insert_action(self, action):
        self.c.execute(
            ('insert into Actions ',
             '(fk_test, started_on, finished_on, description, state) '
             'values (?, ?, ?, ?, ?)'),
            (action.test._id, action.started_on, action.finished_on,
             action.step.method_name, action.state)
        )
        action._id = self.c.lastrowid

    def _insert_measurement(self, measurement, check):
        self.c.execute(
            ('insert into Measurements '
             '(fk_check, char_key, tracking, value) '
             'values (?, ?, ?, ?)'),
            (check._id, measurement.characteristic.key, measurement.tracking,
             measurement.value)
        )

        measurement._id = self.c.lastrowid

    def _insert_defect(self, defect, check):
        self.c.execute(
            ('insert into Defects '
             '(fk_check, failure_key, tracking) '
             'values (? , ?, ?)'),
            (check._id, defect.failure.key, defect.tracking)
        )
        defect._id = self.c.lastrowid


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

    def get_by(self, part_model, serial_number):
        if part_model not in self.session._parts:
            return

        parts = self.session._parts[part_model]
        for part in parts:
            if part.tracking == serial_number:
                return part

    def get_last_serial_number(self, part_model, sn_filter):
        for parts in self.session._parts.values():
            pass


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
        key = (part_model.key, location.key)
        if key in self.session._control_plans:
            return self.session._control_plans[key]

        for group in part_model.part_groups:
            key = (group, location)
            if key in self.sessionn._control_plans:
                return self.session._control_plans[key]


class TestRepo(Repository):
    def add(self, test):
        with self.session.lock:
            self.session._tests.append(test)
