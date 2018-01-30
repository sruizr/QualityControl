from datetime import datetime
import json
import importlib
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import (
    String, Integer, DateTime, Float
    )
from sqlalchemy.orm import relationship, backref
from quactrl.domain.data import DataAccessLayer as Dal


class Pars(Dal.Base):
    __tablename__ = 'pars'
    id = Column(Integer, primary_key=True)
    _pars = Column(String)

    def __init__(self, pars):
        self.set(pars)

    def get(self):
        return json.loads(self._pars)

    def set(self, value):
        self._pars = json.dumps(value)


class WithPars:
    @declared_attr
    def pars_id(cls):
        return Column(Integer, ForeignKey('pars.id'))

    @declared_attr
    def pars(cls):
        return relationship('Pars')

class Resource(Dal.Base, WithPars):
    __tablename__ = 'resource'
    is_a = Column(String)
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    name = Column(String)
    description = Column(String)

    def __init__(self, key, description=''):
        self.key = key
        self.description = description


class ResourceRelation(Dal.Base):
    __tablename__ = 'resource_relation'

    id = Column(Integer, primary_key=True)
    relation_class = Column(String, default='contain')
    from_resource_id = Column(Integer, ForeignKey('resource.id'))
    to_resource_id = Column(Integer, ForeignKey('resource.id'))
    qty = Column(Float, default=1.0)

    from_resource = relationship('Resource', foreign_keys=[from_resource_id],
                                 backref='destinations')
    to_resource = relationship('Resource', foreign_keys=[to_resource_id])



class Node(Dal.Base):
    __tablename__ = 'node'
    is_a = Column(String)
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    name = Column(String)

    def __init__(self, key, name=None):
        self.key = key
        self.name = name


class NodeRelation(Dal.Base):
    __tablename__ = 'node_relation'
    id = Column(Integer, primary_key=True)
    relation_class = Column(String, default='contains')
    qty = Column(Float, default=1.0)
    from_node_id = Column(Integer, ForeignKey('node.id'))
    to_node_id = Column(Integer, ForeignKey('node.id'))

    from_node = relationship('Node', foreign_keys=[from_node_id],
                             backref='destinations')
    to_node = relationship('Node', foreign_keys=[to_node_id], backref='sources')

    def __init__(self, from_node, to_node, relation='contains', qty=1.0):
        self.from_node = from_node
        self.to_node = to_node
        self.relation_class = relation
        self.qty = qty


class Item(Dal.Base, WithPars):
    __tablename__ = 'item'
    is_a = Column(String)
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    resource_id = Column(ForeignKey('resource.id'))
    resource = relationship("Resource")
    tracking = Column(String, index=True)
    state = Column(String, index=True, default='active')

    def __init__(self, resource, tracking='', state='active', path=None):
        self.resource = resource
        self.tracking = tracking
        self.state = state

        if path:
            path.insert_item(self)

class ItemRelation(Dal.Base):
    __tablename__ = 'item_relation'
    id = Column(Integer, primary_key=True)
    relation_class = Column(String, default='has')
    from_item_id = Column(Integer, ForeignKey('item.id'))
    to_item_id = Column(Integer, ForeignKey('item.id'))
    qty = Column(Float, default=1.0)

    from_item = relationship('Item', foreign_keys=[from_item_id], backref='destinations')
    to_item = relationship('Item', foreign_keys=[to_item_id])


class Path(Dal.Base, WithPars):
    __tablename__ = 'path'
    is_a = Column(String(15))
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('path.id'))
    sequence = Column(Integer, default=0)
    method_name = Column(String(30), default='')
    parameters = Column(String, default='{}')
    from_node_id = Column(Integer, ForeignKey('node.id'), index=True)
    to_node_id = Column(Integer, ForeignKey('node.id'), index=True)

    from_node = relationship('Node', foreign_keys=[from_node_id])
    to_node = relationship('Node', foreign_keys=[to_node_id])
    children = relationship('Path',
                            backref=backref('parent', remote_side=[id]),
                            order_by= 'Path.sequence'
                            )


    def insert_item(self, item, qty=1.0, user=None):
        Movement(item=item, from_node=self.from_node, qty=qty, path=self, user=user)

    def move_item(self, item):
        pass

    def add_step(self, step):
        new_seq = self.children[-1].sequence + 5 if self.children else 0
        step.sequence = new_seq
        self.children.append(step)

    def add_resource(self, resource, flow='inout', qty=1.0):
        path_resource = PathResource(
            path=self,
            resource=resource
        )
        path_resource.flow = flow
        path_resource.qty = qty

    def get_parameters(self):
        return json.loads(self.parameters)

    def set_parameters(self, value):
        self.parameters = json.dumps(value)


class PathResource(Dal.Base, WithPars):
    __tablename__ = 'path_resource'

    id = Column(Integer, primary_key=True)
    resource_id = Column(Integer, ForeignKey('resource.id'))
    path_id = Column(Integer, ForeignKey('path.id'), index=True)
    flow = Column(String(10), default='inout')
    qty = Column(Float, default=1.0)

    path = relationship('Path', backref='resource_list')
    resource = relationship('Resource')

    def __init__(self, path, resource, pars=None):
        self.resource = resource
        self.path = path
        if pars:
            self.pars = Pars(pars)


class Movement(Dal.Base):
    __tablename__ = 'movement'
    id = Column(Integer, primary_key=True)
    item_id = Column(ForeignKey('item.id'), nullable=False)
    from_node_id = Column(Integer, ForeignKey('node.id'), index=True)
    to_node_id = Column(Integer, ForeignKey('node.id'), index=True)
    user_id = Column(Integer, ForeignKey('node.id'))

    path_id = Column(Integer, ForeignKey('path.id'))
    input_on = Column(DateTime, default=datetime.now)
    output_on = Column(DateTime)
    qty = Column(Float, default=1.0)

    from_node = relationship('Node', foreign_keys=[from_node_id])
    to_node = relationship('Node', foreign_keys=[to_node_id])
    user = relationship('Node', foreign_keys=[user_id])
    item = relationship('Item', backref='movements')
    path = relationship('Path')


class DataAccessModule:
    _methods = {}

    def __init__(self, dal):
        self.dal = dal

    def get_method(self, path):
        method_name = path.method_name
        if method_name:
            if method_name in self._methods:
                return self._methods[method_name]
            else:
                modules = method_name.split('.')
                module = importlib.import_module('.'.join(modules[:-1]))
                method = getattr(module, modules[-1], None)
                if method:
                    self._methods[method_name] = method
                    return method
