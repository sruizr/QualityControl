import re
import quactrl.models.core as core
import quactrl.models.devices as devs
import quactrl.models.documents as docs
import quactrl.models.hhrr as hr
import quactrl.models.operations as ops
import quactrl.models.products as prd
import quactrl.models.quality as qua
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Base:
    def __init__(self, dal):
        """Base class for a repositry class with session pattern
        """
        self.dal = dal

    @property
    def session(self):
        return self.dal.Session()

    def add(self, obj):
        self.session.add(obj)

    def remove(self, obj):
        self.session.delete(obj)

    def create(self, *args, **kwargs):
        raise NotImplementedError


class FormRepo(Base):
    def create(self, key, template_name, description, pars=None):
        return docs.Form(key, template_name, description, pars)


class DirectoryRepo(Base):
    def create(self, key, name, description=None, parent_key=None):
        parent = (None if parent_key is None
                  else self.dal.Directorys().get(parent_key))
        return docs.Directory(key, name, description, parent)


class ControlPlanRepo(Base):
    def create(self, from_location_key, to_location_key, role_key,
               output_keys):

        source = self.dal.Locations().get(from_location_key)
        destination = self.dal.Locations().get(to_location_key)
        role = self.dal.Roles().get(role_key)
        outputs = []
        for key in output_keys:
            resource = self.dal.PartGroups().get(key)
            if not resource:
                resource = self.dal.PartModels().get(key)
            outputs.append(resource)

        logger.debug('Creating control plan with {}, {}, {}'.format(
            source.key, destination.key, role
        ))
        return qua.ControlPlan(source, destination, role, outputs)


class PartGroupRepo(Base):
    def create(self, key, name, pars=None):
        return prd.PartGroup(key=key, name=name, pars=pars)


class PartModelRepo(Base):
    def create(self, key, name, description, group_keys=None):
        groups = []
        if group_keys:
            for group_key in group_keys:
                groups.append(self.dal.PartGroups().get(group_key))

        return prd.PartModel(part_number=key, name=name,
                             description=description,
                             groups=groups)


class PartRepo(Base):
    pass


class TestRepo(Base):
    pass


class MeasurementRepo(Base):
    pass


class LocationRepo(Base):
    def create(self, key, name, description):
        return ops.Location(key, name, description)


class StepRepo(Base):
    _CLASSES = {
        '.doc.': docs.AdminStep,
        '.qua.': qua.Control,
        '.setup.': ops.Step
    }

    def create(self, route, method, pars=None, source_key=None,
               destination_key=None, output_keys=None):
        node_repo = (self.dal.Locations() if '.doc.' in method
                     else self.dal.Directorys())
        for key, Step in self._CLASSES.items():
            if key in method:
                step = Step(route, method, pars)
                step.source = (node_repo.get(source_key) if source_key
                               else None)
                step.destination = (node_repo.get(destination_key)
                                    if destination_key else None)
                if output_keys:  # Only allowed forms
                    for key in output_keys:
                        step.outputs.append(self.dal.Forms().get(key))
        return step


class FlowRepo(Base):
    def create(self, responsible_key):
        responsible = self.dal.Persons().get(responsible_key)
        return core.Flow(responsible)


class PersonRepo(Base):
    def create(self, key, name, description, role_keys=None):
        roles = []
        if role_keys:
            for role_key in role_keys:
                roles.append(self.dal.Roles().get(role_key))

        return hr.Person(key, name, description, roles)


class RoleRepo(Base):
    def create(self, key, name, description, person_keys=None):
        persons = []
        if person_keys:
            for person_key in person_keys:
                persons.append(self.dal.Persons().get(person_key))

        logger.debug("Creating role with {},{},{}, {}".format(
            key, name, description, persons
        ))
        return hr.Role(key, name, description, persons)


class RequirementRepo(Base):
    _char_pattern = re.compile(r'(\w+@\w+)')

    def create(self, key, specs, name=None, description=None):
        char_key = self._char_pattern.findall(key)[0]
        characteristic = self.dal.Characteristics().get(char_key)
        return prd.Requirement(characteristic, key, specs=specs)


class CharacteristicRepo(Base):
    _char_pattern = re.compile(r'(\w+)@(\w+)')

    def create(self, key, mode_keys=None):
        match = self._char_pattern.match(key)
        attribute = self.dal.Attributes().get(match.groups()[0])
        element = self.dal.Elements().get(match.groups()[1])
        characteristic = prd.Characteristic(key=key,
                                            element=element,
                                            attribute=attribute)

        # logger.debug('insertando {} en characteristic'.format(mode_keys))
        mode_keys = [] if mode_keys is None else mode_keys
        for mode_key in mode_keys:
            mode = self.dal.Modes().get(mode_key)
            characteristic.add_failure_mode(mode)

        return characteristic


class DeviceModelRepo(Base):
    def create(self, key, name, description, pars):
        return devs.DeviceModel(key, name, description, pars)


class DeviceRepo(Base):
    def create(self, device_model_key, tracking, pars=None):
        device_model = self.dal.DeviceModels().get(device_model_key)
        if device_model is None:
            raise Exception('Not found device model with key {}'.format(
                device_model_key
            ))
        return devs.Device(device_model, tracking, pars)


class ElementRepo(Base):
    def create(self, key, name, description=None, parent_key=None):
        parent = self.dal.Elements().get(parent_key) if parent_key else None
        return prd.Element(key, name, description, parent)


class AttributeRepo(Base):
    def create(self, key, name, description=None):
        return prd.Attribute(key, name, description)


class ModeRepo(Base):
    def create(self, key, name, description=None):
        return qua.Mode(key, name)
