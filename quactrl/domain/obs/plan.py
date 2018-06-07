import enum
from sqlalchemy.types import Enum, String
from sqlalchemy.orm import synonym, reconstructor, aliased
from quactrl.domain.base import (Node, Path, Resource, ResourceRelation,
                                PathResource, Token, Item)
from quactrl.domain import get_component
from sqlalchemy.orm import reconstructor


class Operation(Path):
    __mapper_args__ = {'polymorphic_identity': 'operation'}




class PartGenerator(Path):
    def __init__(self, method_name='quactrl.methods.gen_part', **kwargs):
        Path.__init__(self, method_name=method_name, **kwargs)


class Generator(Path):
    def __init__(self, to_node, method_name, **kwargs):
        Path.__init__(self, from_node=None, to_node=to_node,
                      method_name=method_name, **kwargs)


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
