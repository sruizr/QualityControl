import enum
from sqlalchemy.types import Enum, String
from sqlalchemy.orm import synonym, reconstructor, aliased
from quactrl.domain.erp import (Node, Path, Resource, ResourceRelation,
                                PathResource, Token, Item)
from quactrl.domain import get_component
from sqlalchemy.orm import reconstructor


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


class PartGenerator(Path):
    def __init__(self, method_name='quactrl.methods.gen_part', **kwargs):
        Path.__init__(self, method_name=method_name, **kwargs)


class Generator(Path):
    def __init__(self, to_node, method_name, **kwargs):
        Path.__init__(self, from_node=None, to_node=to_node,
                      method_name=method_name, **kwargs)

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


class DataAccessModule:
    """Operate with plan Entities"""
    def __init__(self, dal):
        self.dal = dal

    def get_avalaible_tokens(self, node_key, item_args, session=None):
        #session = self.dal.Session() if session is None else session
        qry = session.query(Token).join(Node).join(Item)

        filters = [Node.key == node_key]
        if 'resource_key' in item_args:
            qry = qry.join(Resource)
            filters.append(Resource.key == item_args['item_resource_key'])

        if 'tracking' in item_args:
            filters.append(Item.tracking == item_args['tracking'])

        return qry.filter(*filters).all()

    def get_path(self, args, session=None):
        """Return process by key, None if not exist"""
        # session = self.dal.Session() if session is None else session

        qry = session.query(Path)

        filters = []
        if 'name' in args:
            filters.append(Path.name.contains(args['name']))
        if 'from_node_key' in args:
            FromNode = aliased(Node)
            qry = qry.join(FromNode, Path.from_node)
            filters.append(FromNode.key == args['from_node_key'])
        if 'to_node_key' in args:
            ToNode = aliased(Node)
            qry = qry.join(ToNode, Path.to_node)
            filters.append(ToNode.key == args['to_node_key'])

        return qry.filter(*filters).first()

    # def get_operation(self, method_name, partnumber):
    #     session = self.dal.Session()
    #     operation = session.query(Operation).join(PathResource).join(Resource).filter(
    #         Operation.method_name == method_name,
    #         Resource.key == partnumber
    #         ).first()

    #     return operation

    # def get_generator_by_location(self, location):
    #     session = self.dal.session
    #     query = session.query(Operation).filter(
    #         Operation.to_node == location,
    #         Operation.method_name.contains('generator')
    #         )
    #     return query.first()

    # def get_operation_by_location(self, location, resource_key, method_name):
    #     pass

    # def get_process(self, method_name, resource):
    #     session = self.dal.Session()
    #     process = session.query(Process).join(PathResource).filter(
    #         Process.method_name == method_name,
    #         PathResource.resource == resource
    #         ).first()
    #     return process

    def get_part_model_by_key(self, key, session=None):
        # session = self.dal.Session() if session is None else session

        return session.query(PartModel).filter(PartModel.key==key).one()
