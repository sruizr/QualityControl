from .base import Resource, ResourceRelation
from sqlalchemy.orm import reconstructor


class Characteristic(Resource):
    __mapper_args__ = {'polymorphic_identity': 'characteristic'}

    def __init__(self, key, description):
        self.key = key
        self.description = description
        self._failure_modes = {}

    def add_failure_mode(self, mode):
        self.get_failure_mode(mode)

    def get_failure_mode(self, mode):
        if mode not in self._failure_modes:
            failure_mode = FailureMode(mode, self)
            self._failure_modes[mode] = failure_mode

        return self._failure_modes[mode]

    @reconstructor
    def after_load(self):
        self._failure_modes = {}
        for destination in self.destinations:
            if destination.to_resource.is_a == 'failure_mode':
                mode = destination.to_resource.key.split('-')[0]
                self._failure_modes[mode] = destination.to_resource



class FailureMode(Resource):
    __mapper_args__ = {'polymorphic_identity': 'failure_mode'}

    def __init__(self, mode, characteristic):

        key = '{}-{}'.format(mode, characteristic.key)
        description = '{} {}'.format(mode, characteristic.description)
        Resource.__init__(self, key, '', description)

        rl = ResourceRelation(relation_class='contains', to_resource=self)
        characteristic.destinations.append(rl)


class DeviceModel(Resource):
    __mapper_args__ = {'polymorphic_identity': 'device_model'}


class PartModel(Resource):
    __mapper_args__ = {'polymorphic_identity': 'part_model'}

    _dut_classes = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._load_dut_class()

    def _load_dut_class(self):
        if self.pars:
            pars = self.pars.get()
            if self.key not in self._dut_classes:
                class_name = pars.pop('class_name')
                Dut = get_component(class_name)
                self._dut_classes[self.key] = (Dut, pars)

    @reconstructor
    def after_load(self):
        self._load_dut_class()

    def get_behaviour(self):
        if self.key in self._dut_classes:
            Dut = self._dut_classes[self.key][0]
            pars = self._dut_classes[self.key][1]

            return Dut(**pars)
