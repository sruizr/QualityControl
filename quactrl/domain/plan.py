import enum
from sqlalchemy.types import Enum, String
from sqlalchemy.orm import synonym, reconstructor
from quactrl.domain.erp import (Node, Path, Resource, ResourceRelation,
                                PathResource)


class Operation(Path):
    __mapper_args__ = {'polymorphic_identity': 'operation'}


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
            if destination.is_a == 'failure_mode':
                mode = destination.resource.description.split('-')[0]
                self._failure_modes[mode] = destination.resource


class FailureMode(Resource):
    __mapper_args__ = {'polymorphic_identity': 'failure_mode'}

    def __init__(self, mode, characteristic):
        self.key = '{}-{}'.format(mode[:3], characteristic.key)
        self.description = '{} {}'.format(mode, characteristic.description)
        ResourceRelation(characteristic, self)


class PartModel(Resource):
    __mapper_args__ = {'polymorphic_identity': 'part_model'}


class DeviceModel(Resource):
    __mapper_args__ = {'polymorphic_identity': 'device_model'}


class DataAccessModule:
    """Operate with plan Entities"""
    def __init__(self, dal):
        self.dal = dal

    def get_operation(self, method_name, partnumber):
        session = self.dal.Session()
        operation = session.query(Operation).join(PathResource).join(Resource).filter(
            Operation.method_name == method_name,
            Resource.key == partnumber
            ).first()

        return operation

    def get_generator_by_location(self, location):
        session = self.dal.session
        query = session.query(Operation).filter(
            Operation.to_node == location,
            Operation.method_name.contains('generator')
            )
        return query.first()

    def get_operation_by_location(self, location, resource_key, method_name):
        pass

    def get_process(self, method_name, resource):
        session = self.dal.Session()
        process = session.query(Process).join(PathResource).filter(
            Process.method_name == method_name,
            PathResource.resource == resource
            ).first()
        return process
