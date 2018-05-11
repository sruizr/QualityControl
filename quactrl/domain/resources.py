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
