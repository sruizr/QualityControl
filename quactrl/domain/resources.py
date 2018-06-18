from .base import Resource, ResourceRelation, Pars
from sqlalchemy.orm import reconstructor, relationship
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property


class IsA(ResourceRelation):
    """A member is a group"""
    __mapper_args__ = {'polymorphic_identity': 'is_a'}

    def __init__(self, member, group, pars=None):
        self.from_resource = member
        self.to_resource = group
        if pars:
            self.pars = Pars(pars)

    @hybrid_property
    def group(self):
        return self.to_resource

    @hybrid_property
    def member(self):
        return self.from_resource

    @group.setter
    def group(self, group):
        self.to_resource = group

    @member.setter
    def member(self, member):
        self.from_resource = member


class Composition(ResourceRelation):
    """A system contains a component"""
    __mapper_args__ = {'polymorphic_identity': 'contains'}

    def __init__(self, system, component, qty=1.0):
        self.from_resource = system
        self.to_resource = component
        self.qty = qty

    @hybrid_property
    def component(self):
        return self.to_resource

    @hybrid_property
    def system(self):
        return self.from_resource

    @component.setter
    def component(self, component):
        self.to_resource = component

    @system.setter
    def system(self, system):
        self.from_resource = system


class Requirement(ResourceRelation):
    """A resource requires a characteristic"""
    __mapper_args__ = {'polymorphic_identity': 'requires'}

    @hybrid_property
    def specs(self):
        return self.pars

    @specs.setter
    def specs(self, specs):
        self.pars.dict  = specs

    def __init__(self, resource, characteristic, specs=None):
        self.from_resource = resource
        self.to_resource = characteristic
        if specs:
            self.pars = Pars(**specs)

    @hybrid_property
    def characteristic(self):
        return self.to_resource

    @characteristic.setter
    def characteristic(self, char):
        self.to_resource = char

    def get_requirement_by_characteristic(self, characteristic):
        if characteristic == self.characteristic:
            return self
        else:
            for req in self.characteristic.requirements:
                requirement = req.get_requirement()
                if req.characteristic == characteristic:
                    return req


class Failure(ResourceRelation):
    """A characteristic fails with a mode"""
    __mapper_args__ = {'polymorphic_identity': 'fails'}

    def __init__(self, characteristic, mode_key, mode=None):
        for failure in characteristic.failures:
            if failure.failure_mode.key == '{}-{}'.format(
                    mode_key, characteristic.key):
                raise DuplicatedFailure(
                    'Characteristic "{}" has duplicated failures mode {}'.format(
                        characteristic.description, mode
                    ))

        self.from_resource = characteristic
        self.to_resource = FailureMode(characteristic, mode_key)

    @hybrid_property
    def failure_mode(self):
        return self.to_resource

    @failure_mode.setter
    def failure_mode(self, value):
        self.to_resource = value


class WithMembers:
    @declared_attr
    def members(cls):
        return relationship('IsA', foreign_keys=[IsA.to_resource_id])


class WithRequirements:
    @declared_attr
    def requirements(cls):
        return relationship('Requirement',
                            foreign_keys=[Requirement.from_resource_id])

    def get_requirement_by_characteristic(self, characteristic):
        for req in self.requirements:
            if req.characteristic == characteristic:
                return req

class WithComponents:
    @declared_attr
    def components(cls):
        return relationship('Composition',
                            foreign_keys=[Composition.from_resource_id])

    def __getitem__(self, key):
        for composition in self.components:
            if composition.component.key == key:
                return composition.component


class WithGroups:
    @declared_attr
    def groups(cls):
        return relationship('IsA', foreign_keys=[IsA.from_resource_id])

    def get_pars_from_group(self, name):
        pars = None
        for group in self.groups:
            if group.group.name == name:
                pars = group.pars.dict
        return pars


class Characteristic(Resource, WithRequirements):
    __mapper_args__ = {'polymorphic_identity': 'characteristic'}

    failures = relationship('Failure',
                            foreign_keys=[Failure.from_resource_id])

    def __init__(self, key, description=''):
        self.key = key
        self.description = description

    def get_or_create_failure_mode(self, mode_key):
        failure_mode_key = self._compose_failure_mode_key(mode_key)

        for failure in self.failures:
            if failure.failure_mode.key == failure_mode_key:
                return failure.failure_mode
        failure_mode = Failure(self, mode_key).failure_mode

        return failure_mode

    def _compose_failure_mode_key(self, mode_key):
        return '{}-{}'.format(mode_key, self.key)


class DuplicatedFailure(Exception):
    pass


class FailureMode(Resource):
    __mapper_args__ = {'polymorphic_identity': 'failure_mode'}

    def __init__(self, characteristic, mode_key, mode=None):
        key = '{}-{}'.format(mode_key, characteristic.key)
        self.key = key
        self.name = key

        mode = mode if mode else mode_key
        self.description = '{}, {}'.format(characteristic.description, mode)


class DeviceModel(Resource):
    __mapper_args__ = {'polymorphic_identity': 'device_model'}

    def get_configuration(self):
        return self.get_pars_from_group('device')

class Form(Resource):
    __mapper_args__ = {'polymorphic_identity': 'form'}


class PartGroup(Resource, WithMembers, WithGroups, WithRequirements):
    __mapper_args__ = {'polymorphic_identity': 'part_group'}

class DeviceGroup(Resource, WithMembers, WithGroups):
    __mapper_args__ = {'polymorphic_identity': 'device_group'}

class PartModel(Resource, WithGroups, WithComponents, WithRequirements):
    __mapper_args__ = {'polymorphic_identity': 'part_model'}

    def get_configuration(self):
        return self.get_pars_from_group('device')



class Document(Resource, WithGroups):
    __mapper_args__ = {'polymorphic_identity': 'report'}

    def get_template(self):
        """Return parameters to be filled by the report"""
        return self.get_pars_from_group('template')

        # _dut_classes = {}


    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self._load_dut_class()

    # def _load_dut_class(self):
    #     if self.pars:
    #         pars = self.pars.get()
    #         if self.key not in self._dut_classes:
    #             class_name = pars.pop('class_name')
    #             Dut = get_component(class_name)
    #             self._dut_classes[self.key] = (Dut, pars)

    # @reconstructor
    # def after_load(self):
    #     self._load_dut_class()

    # def get_behaviour(self):
    #     if self.key in self._dut_classes:
    #         Dut = self._dut_classes[self.key][0]
    #         pars = self._dut_classes[self.key][1]

    #         return Dut(**pars)
