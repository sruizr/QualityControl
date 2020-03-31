from threading import Lock
import quactrl.data.repositories as reps
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Session:
    _Route = {}
    _Person = {}
    _Location = {}
    _PartModel = {}
    _Attribute = {}
    _Element = {}
    _Mode = {}
    _PartGroup = {}
    _ControlPlan = []
    _Device = []
    _DeviceModel = {}
    _Test = []
    _Role = {}
    _Part = []
    _Requirement = {}
    _Characteristic = {}
    _Form = {}
    _Directory = {}
    _lock = Lock()
    _Flow = []


    def _repo(self, obj):
        return getattr(self, '_{}'.format(obj.__class__.__name__))

    def add(self, obj):
        repo = self._repo(obj)
        with self._lock:
            if type(repo) is dict:
                repo[obj.key] = obj
            elif type(repo) is list:
                repo.append(obj)

    def delete(self, obj):
        with self._lock:
            repo = self._repo(obj)
            if type(repo) is dict:
                repo.pop(obj.key)
            elif type(repo) is list:
                repo.remove(obj)

    def commit(self):
        pass

    def rollback(self):
        pass


class Database:
    def __init__(self, connection_string, **kwargs):
        "docstring"
        pass

    @property
    def Session(self):
        """Session class with thread locking capabilities
        """
        return Session


class DeviceRepo(reps.DeviceRepo):
    def get_all_from(self, location_key):
        return [device for device in self.session._Device]


class PartRepo(reps.PartRepo):
    def get_by(self, part_model, serial_number):
        for part in self.session._Part:
            if part.model == part_model and part.serial_number == serial_number:
                return part

    def get_last_serialnumber(self, partmodel, batchnumber, pos):
        """Retrieve the last serial number from dalbase (if exists...)
        """
        serial_numbers = [int(part.serial_number)
                          for part in self.session._Part
                          if (part.model == partmodel) and
                          (part.serial_number[4:10] == batchnumber)]
        if serial_numbers:
            return str(max(serial_numbers))


class ControlPlanRepo(reps.ControlPlanRepo):
    def get_by(self, part_model, location):
        """Return control plan for a partmodel on a location
        """
        for control_plan in self.session._ControlPlan:
            logger.debug('Control plan source is {}'.format(control_plan.source.key))
            if control_plan.source == location:
                if part_model in control_plan.outputs:
                    return control_plan
                else:
                    for group in part_model.groups:
                        if group in control_plan.outputs:
                            return control_plan


class MeasurementRepo(reps.MeasurementRepo):
    def get_all_from(self, check):
        return check.measurements


class _KeyRepo:
    def get(self, key):
        repo_name = '_{}'.format(self.__class__.__name__[:-4])
        repo = getattr(self.session, repo_name)
        # logger.debug('There are {} items on repository {}'.format(len(repo),
        #                                                           repo_name))
        return repo.get(key)


class AttributeRepo(reps.AttributeRepo, _KeyRepo):
    pass


class ElementRepo(reps.ElementRepo, _KeyRepo):
    pass


class ModeRepo(reps.ModeRepo, _KeyRepo):
    pass


class LocationRepo(reps.LocationRepo, _KeyRepo):
    pass


class PartGroupRepo(reps.PartGroupRepo, _KeyRepo):
    pass


class PersonRepo(reps.PersonRepo, _KeyRepo):
    pass


class RoleRepo(reps.RoleRepo, _KeyRepo):
    pass


class CharacteristicRepo(reps.CharacteristicRepo, _KeyRepo):
    pass


class DeviceModelRepo(reps.DeviceModelRepo, _KeyRepo):
    pass


class RequirementRepo(reps.RequirementRepo, _KeyRepo):
    pass


class PartModelRepo(reps.PartModelRepo, _KeyRepo):
    pass


class FlowRepo(reps.FlowRepo):
    pass


class StepRepo(reps.StepRepo):
    pass


class DirectoryRepo(reps.DirectoryRepo, _KeyRepo):
    pass


class TestRepo(reps.TestRepo):
    pass
