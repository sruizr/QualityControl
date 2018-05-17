import json
import importlib
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import (
    String, Integer, DateTime, Float
    )
from sqlalchemy.orm import relationship, backref, reconstructor, aliased
from quactrl.domain import Base, get_component


class Pars(Base):
    __tablename__ = 'pars'
    id = Column(Integer, primary_key=True)
    _pars = Column(String(1000))

    def __init__(self, pars):
        self.set(pars)

    def get(self):
        if self._pars:
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
    is_a = Column(String(30))
    __mapper_args__  = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True)
    name = Column(String(100), default='')
    description = Column(String(100), default='')

    def __init__(self, key, name, description, pars=None):
        Base.__init__(self, key=key, name=name, description=description)
        if pars:
            self.pars = Pars(pars)

class ResourceRelation(Base):
    __tablename__ = 'resource_relation'

    id = Column(Integer, primary_key=True)
    relation_class = Column(String(100), default='bypass')
    from_resource_id = Column(Integer, ForeignKey('resource.id'))
    to_resource_id = Column(Integer, ForeignKey('resource.id'))
    qty = Column(Float, default=1.0)

    from_resource = relationship('Resource', foreign_keys=[from_resource_id],
                                 backref='destinations')
    to_resource = relationship('Resource', foreign_keys=[to_resource_id])


class Node(Base):
    __tablename__ = 'node'
    is_a = Column(String(30))
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True)
    name = Column(String(50))
    description = Column(String(200))

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
    relation_class = Column(String(100), default='contains')
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
    is_a = Column(String(30))
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    resource_id = Column(ForeignKey('resource.id'))
    resource = relationship("Resource")
    tracking = Column(String(100), index=True)
    state = Column(String(100), index=True, default='active')

    def __init__(self, resource, tracking='', state='active', pars=None):
        self.resource = resource
        self.tracking = tracking
        self.state = state
        if pars:
            self.pars = Pars(pars)

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
    relation_class = Column(String(100), default='has')
    from_item_id = Column(Integer, ForeignKey('item.id'))
    to_item_id = Column(Integer, ForeignKey('item.id'))
    qty = Column(Float, default=1.0)

    from_item = relationship('Item', foreign_keys=[from_item_id], backref='destinations')
    to_item = relationship('Item', foreign_keys=[to_item_id])


class Path(Base, WithPars):
    __tablename__ = 'path'
    is_a = Column(String(15))
    created_on = Column(DateTime, default=datetime.now)
    removed_on = Column(DateTime)
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('path.id'))
    sequence = Column(Integer, default=0)
    name = Column(String(100), default='')
    method_name = Column(String(100), default='')
    from_node_id = Column(Integer, ForeignKey('node.id'), index=True)
    to_node_id = Column(Integer, ForeignKey('node.id'), index=True)

    from_node = relationship('Node', foreign_keys=[from_node_id])
    to_node = relationship('Node', foreign_keys=[to_node_id])
    children = relationship('Path',
                            backref=backref('parent', remote_side=[id]),
                            order_by='Path.sequence'
                            )


    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)
        self._load_resources()

    def _load_resources(self):
        self.in_resources = {}
        self.out_resources = {}

        for path_resource in self.resource_list:
            if path_resource.flow in ('inout', 'in'):
                self.in_resources[path_resource.resource.key] = (
                    path_resource.resource, path_resource.qty
                )
            if path_resource.flow in ('inout', 'out'):
                self.out_resources[path_resource.resource.key] = (
                    path_resource.resource, path_resource.qty
                )

    @reconstructor
    def after_load(self):
        self._load_resources()

    def append_step(self, step_path):
        new_seq = self.children[-1].sequence + 5 if self.children else 0
        step_path.sequence = new_seq
        step_path.parent = self
        step_path.from_node = self.from_node
        step_path.to_node = self.from_node

    def add_resource(self, resource, flow='inout', qty=1.0):
        self.resource_list.append(PathResource(
            path=self,
            resource=resource,
            flow=flow
        ))
        self._load_resources()

    def accept_inputs(self, inputs):
        #  TODO:
        return True

    def create_flow(self, responsible, controller=None):
        return Flow(path=self,
                    responsible=responsible,
                    controller=controller)


class PathResource(Base, WithPars):
    __tablename__ = 'path_resource'

    id = Column(Integer, primary_key=True)
    resource_id = Column(Integer, ForeignKey('resource.id'))
    path_id = Column(Integer, ForeignKey('path.id'), index=True)
    flow = Column(String(10), default='inout')
    qty = Column(Float, default=1.0)

    path = relationship('Path', backref='resource_list')
    resource = relationship('Resource')

    def __init__(self, path, resource, flow, qty=1.0,  pars=None):
        self.resource = resource
        self.path = path
        self.flow = flow
        self.qty = qty
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

    node = relationship('Node')
    flow = relationship('Flow', backref='out_tokens')
    item = relationship('Item')



    def encode(self):
        return {'resource_key': self.item.resource.key,
                'tracking': self.item.tracking,
                'qty': self.qty,
                'state':self.state,
                'flow_id': self.flow_id,
                'id': self.id
        }


class Flow(Base):
    __tablename__ = 'flow'
    id = Column(Integer, primary_key=True)
    is_a = Column(String(15))
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    started_on = Column(DateTime, default=datetime.now)
    path_id = Column(Integer, ForeignKey('path.id'))
    parent_id = Column(Integer, ForeignKey('flow.id'))
    responsible_id = Column(Integer, ForeignKey('node.id'))
    finished_on = Column(DateTime)
    state = Column(String(15), default='ongoing')

    responsible = relationship('Node')
    path = relationship('Path')
    children = relationship('Flow',
                            backref=backref('parent', remote_side=[id])
                           )

    def __init__(self,  **kwargs):
        self.controller = kwargs.pop('controller')
        super().__init__(**kwargs)
        self._load_fields()

    def _load_fields(self):
        self.method = None
        try:
            self.method = get_component(self.path.method_name)
        except Exception as e:
            pass
        self.inputs = []
        self.outputs = []
        self.in_tokens = []
        self.out_tokens = []

    @reconstructor
    def after_load(self):
        self._load_fields()

    def prepare(self):
        # TODO
        self.started_on = datetime.now()

    def execute(self):
        if self.method:
            self.method(self, self.controller)

    def terminate(self):
        for token in self.in_tokens:
            token.state = 'consumed'

        # (item, qty)
        for output in self.outputs:
            Token(
                item= output[0],
                qty=output[1],
                node=self.path.to_node,
                flow=self,
                state='avalaible'
            )

        self.finished_on = datetime.now()
        self.state = 'done'

    def cancel(self):

        self.finished_on = datetime.now()
        self.state = 'cancelled'


class DataAccessModule:
    _methods = {}

    def __init__(self, dal):
        self.dal = dal
    def get_stocks_by_node(self, node, session=None):
        session = self.dal.Session() if session is None else session

        qry = session.query(Token).filter(
            Token.node == node,
            Token.state == 'avalaible'
            )

        return qry.all()
