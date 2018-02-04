import json
import importlib
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import (
    String, Integer, DateTime, Float
    )
from sqlalchemy.orm import relationship, backref, reconstructor
from quactrl.domain import Base, get_component


class Pars(Base):
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


class Resource(Base, WithPars):
    __tablename__ = 'resource'
    is_a = Column(String)
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    name = Column(String)
    description = Column(String)

    def __init__(self, key, description='', **pars):
        self.key = key
        self.description = description
        if pars:
            self.pars = Pars(pars)


class ResourceRelation(Base):
    __tablename__ = 'resource_relation'

    id = Column(Integer, primary_key=True)
    relation_class = Column(String, default='bypass')
    from_resource_id = Column(Integer, ForeignKey('resource.id'))
    to_resource_id = Column(Integer, ForeignKey('resource.id'))
    qty = Column(Float, default=1.0)

    from_resource = relationship('Resource', foreign_keys=[from_resource_id],
                                 backref='destinations')
    to_resource = relationship('Resource', foreign_keys=[to_resource_id])


class Node(Base):
    __tablename__ = 'node'
    is_a = Column(String)
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    name = Column(String)

    inventory = None # TODO

    def __init__(self, key, name=None):
        self.key = key
        self.name = name

    def add_item(self, item, qty=1.0, path=None, responsible=None):
        pass #TODO

    def remove_item(self, item, qty=1.0, path=None, responsible=None):
        pass #TODO

class NodeRelation(Base):
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


class Item(Base, WithPars):
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

    def get_stocks(self):
        stocks = {}
        for movement in self.movements:
            if movement.output_on is None:
                node = movement.from_node
                if not stocks.get(node):
                    stocks[node] = 0
                stocks[node] += movement.qty

        return stocks

class ItemRelation(Base):
    __tablename__ = 'item_relation'
    id = Column(Integer, primary_key=True)
    relation_class = Column(String, default='has')
    from_item_id = Column(Integer, ForeignKey('item.id'))
    to_item_id = Column(Integer, ForeignKey('item.id'))
    qty = Column(Float, default=1.0)

    from_item = relationship('Item', foreign_keys=[from_item_id], backref='destinations')
    to_item = relationship('Item', foreign_keys=[to_item_id])


class Path(Base, WithPars):
    __tablename__ = 'path'
    is_a = Column(String(15))
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('path.id'))
    sequence = Column(Integer, default=0)
    name = Column(String(30), default='')
    method_name = Column(String(30), default='')
    from_node_id = Column(Integer, ForeignKey('node.id'), index=True)
    to_node_id = Column(Integer, ForeignKey('node.id'), index=True)
    responsible_id = Column(Integer, ForeignKey('node.id'))

    from_node = relationship('Node', foreign_keys=[from_node_id])
    to_node = relationship('Node', foreign_keys=[to_node_id])
    responsible_id = relationship('Node', foreign_keys=[responsible_id])

    children = relationship('Path',
                            backref=backref('parent', remote_side=[id]),
                            order_by='Path.sequence'
                            )

    def __init__(self, **kwargs):
        Base.__init__(**kwargs)
        self._load_method()

    def _load_method(self):
        self.method = None
        self.state = 'pasive'
        try:
            self.method = get_component(self.method_name)
            self.state = 'pasive'
        except Exception as e:
            pass

    @reconstructor
    def after_load(self):
        self._load_method()

    def get_possible_outputs(self):
        outputs = []
        for resource_rel in self.resource_list:
            flow = resource_rel.flow
            if flow == 'by_pass' or flow == 'output':
                outputs.append(resource_rel.resource)
        return outputs

    def generate_item(self, item, qty=1.0):
        if item.resource:
            Movement(item=item, from_node=self.from_node, qty=qty, path=self)

    def move_item(self, item):
        pass

    def destroy_item(self, item, qty=1.0):
        pass

    def start(self):
        pass


    def append_step(self, step_path):
        new_seq = self.children[-1].sequence + 5 if self.children else 0
        step_path.sequence = new_seq
        step_path.parent = self
        step_path.from_node = self.from_node
        step_path.to_node = self.from_node

    def add_step(self, step_path):
        pass

    def add_resource(self, resource, flow='inout', qty=1.0):
        path_resource = PathResource(
            path=self,
            resource=resource
        )
        path_resource.flow = flow
        path_resource.qty = qty

    def accept_inputs(self, resources):
        pass #TODO


class PathResource(Base, WithPars):
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


class Token(Base):
    __tablename__ = 'token'
    id = Column(Integer, primary_key=True)

    item_id = Column(Integer, ForeignKey('item.id'), nullable=False,
                     index=True)
    qty = Column(Float, default=1.0)
    node_id = Column(Integer, ForeignKey('node.id'), index=True)
    state = Column(String(15), default='in_process')
    flow_id = Column(Integer, ForeignKey('flow.id'))

    node = relationship('Node', back_populates='stocks')
    flow = relationship('Flow', backref='out_tokens')
    item = relationship('Item')


class Flow(Base):
    __tablename__ = 'flow'

    id = Column(Integer, primary_key=True)

    started_on = Column(DateTime, default=datetime.now)
    path_id = Column(Integer, ForeignKey('path.id'))
    responsible_id = Column(Integer, ForeignKey('node.id'))
    finished_on = Column(DateTime)

    responsible = relationship('Node')
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
