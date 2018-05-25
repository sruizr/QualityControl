import json
import importlib
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import reconstructor
from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import (
    String, Integer, DateTime, Float
    )
from sqlalchemy.orm import relationship, backref, reconstructor, aliased
from quactrl.domain import Base, get_component


class StockException(Exception):
    pass


class ResponsibleNotAuthorized(Exception):
    pass


class Pars(Base):
    __tablename__ = 'pars'
    id = Column(Integer, primary_key=True)
    _pars = Column(String(64000))

    def __init__(self, **kwargs):
        self._dict_pars = kwargs
        self._dump()

    @reconstructor
    def _load(self):
        if self._pars:
            self._dict_pars = json.loads(self._pars)

    def _dump(self):
        self._pars = json.dumps(self._dict_pars)

    def __setitem__(self, key, value):
        self._dict_pars[key] = value
        self._dump()

    def __getitem__(self, key):
        return self._dict_pars[key]

    @property
    def dict(self):
        self._load()
        return self._dict_pars


class WithPars:
    @declared_attr
    def pars_id(cls):
        return Column(Integer, ForeignKey('pars.id'))

    @declared_attr
    def pars(cls):
        return relationship('Pars')


class Resource(Base):
    __tablename__ = 'resource'
    is_a = Column(String(30))
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True)
    name = Column(String(100), default='')
    description = Column(String(100), default='')

    def __init__(self, **kwargs):
        key = kwargs.pop('key')
        name = kwargs.pop('name', '')
        description = kwargs.pop('description', '')
        Base.__init__(self, key=key, name=name, description=description)
        if kwargs:
            self.pars = Pars(**kwargs)


class ResourceRelation(Base, WithPars):
    __tablename__ = 'resource_relation'
    link = Column(String(100))
    __mapper_args__ = {
        'polymorphic_on': link
    }

    id = Column(Integer, primary_key=True)
    from_resource_id = Column(Integer, ForeignKey('resource.id'))
    to_resource_id = Column(Integer, ForeignKey('resource.id'))
    qty = Column(Float, default=1.0)

    from_resource = relationship('Resource', foreign_keys=[from_resource_id])
    to_resource = relationship('Resource', foreign_keys=[to_resource_id])

    Base

class Node(Base, WithPars):
    __tablename__ = 'node'
    is_a = Column(String(30))
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True)
    name = Column(String(50))
    description = Column(String(250))

    def __init__(self, **kwargs):
        self.key = kwargs.pop('key')
        self.name = kwargs.pop('name', '')
        self.description = kwargs.pop('description', '')
        if kwargs:
            self.pars = Pars(**kwargs)

    def add_item(self, item, qty=1.0, path=None, responsible=None):
        pass #TODO

    def remove_item(self, item, qty=1.0, path=None, responsible=None):
        pass #TODO


class NodeRelation(Base):
    __tablename__ = 'node_relation'
    id = Column(Integer, primary_key=True)
    relation_class = Column(String(100), default='has')
    qty = Column(Float, default=1.0)
    from_node_id = Column(Integer, ForeignKey('node.id'))
    to_node_id = Column(Integer, ForeignKey('node.id'))

    from_node = relationship('Node', foreign_keys=[from_node_id],
                             backref='destinations')
    to_node = relationship('Node', foreign_keys=[to_node_id], backref='sources')

    def __init__(self, from_node, to_node, relation='has', qty=1.0):
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
    avalaible_tokens = relationship(
        'Token',
        primaryjoin="and_(Item.id==Token.item_id, Token.consumer_id == None)")

    def __init__(self, resource, tracking='', state='open', pars=None):
        self.resource = resource
        self.tracking = tracking
        self.state = state
        if pars:
            self.pars = Pars(**pars)

    def get_stocks(self):
        """Group avalaible tokens by nodes"""
        stocks = {}
        for token in self.avalaible_tokens:
            if token.node in stocks.keys():
                stocks[token.node].append(token)
            else:
                stocks[token.node] = [token]

        return stocks

    def produce(self, producer, qty=1):
        """Produce a qty of item at producer destination"""
        self.avalaible_tokens.append(Token(qty=qty, producer=producer, node=producer.destination))

    def consume(self, consumer, qty=None):
        """Cosume a qty of item at consumer origin"""
        stocks = self.get_stocks()
        if consumer.origin not in stocks.keys():
            raise StockException('There is no stock on "{}"'.format(
                consumer.origin.key))

        avalaible_qty = sum([token.qty for token in stocks[consumer.origin]])
        if qty is not None and avalaible_qty < qty:
            raise StockException('qty {} is not avalaible at {}'.format(
                qty,
                consumer.origin.key
            ))


        if qty is None:
            for token in stocks[consumer.origin]:
                token.consume(consumer)
        else:
            for token in stocks[consumer.origin]:
                if qty == 0:
                    break
                if qty >= token.qty:
                    token.consume(consumer)
                    qty -= token.qty
                else:
                    token.consume(consumer, qty)
                    qty = 0


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
    method_name = Column(String(100), default='')
    from_node_id = Column(Integer, ForeignKey('node.id'), index=True)
    to_node_id = Column(Integer, ForeignKey('node.id'), index=True)

    from_node = relationship('Node', foreign_keys=[from_node_id])
    to_node = relationship('Node', foreign_keys=[to_node_id])
    steps = relationship(
        'Path',
        backref=backref('parent', remote_side=[id]),
        order_by='Path.sequence'
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_resources()

    def _load_resources(self):
        self.consumes = {}
        self.produces = {}

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


class PathResource(Base):
    __tablename__ = 'path_resource'

    id = Column(Integer, primary_key=True)
    path_id = Column(Integer, ForeignKey('path.id'), index=True)
    resource_id = Column(Integer, ForeignKey('resource.id'))

    path = relationship('Path', backref='resource_list')
    resource = relationship('Resource')
    key = Column(String(10), nullable=False)
    inout = Column(String(10), default='bypass')
    qty = Column(Float, default=1.0)


class Token(Base):
    __tablename__ = 'token'
    id = Column(Integer, primary_key=True)

    item_id = Column(Integer, ForeignKey('item.id'), nullable=False,
                     index=True)
    node_id = Column(Integer, ForeignKey('node.id'), index=True)
    producer_id = Column(Integer, ForeignKey('flow.id'), index=True)
    consumer_id = Column(Integer, ForeignKey('flow.id'), index=True)

    item = relationship('Item')
    qty = Column(Float, default=1.0)
    node = relationship('Node')

    producer = relationship('Flow', foreign_keys=[producer_id])
    consumer = relationship('Flow', foreign_keys=[consumer_id])

    def consume(self, consumer, qty=None):
        if qty is not None:
            if qty > self.qty:
                raise StockException('Quanty avalible is less than consume request')
            elif qty < self.qty:
                rest = self.qty - qty
                self.item.avalaible_tokens.append(Token(qty=rest, producer=self.producer, node=self.node))
                self.qty = qty

        self.consumer = consumer

    def is_consumed(self):
        return self.consumer is not None


    # def encode(self):
    #     return {'resource_key': self.item.resource.key,
    #             'tracking': self.item.tracking,
    #             'qty': self.qty,
    #             'state': self.state,
    #             'flow_id': self.flow_id,
    #             'id': self.id
    #     }


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
    tracking  = Column(String(100))

    responsible = relationship('Node')
    path = relationship('Path')
    children = relationship('Flow',
                            backref=backref('parent', remote_side=[id])
                           )

    def __init__(self, **kwargs):
        self.controller = kwargs.pop('controller', None)
        super().__init__(**kwargs)
        self._load_fields()

    def _load_fields(self):
        self.method = None
        try:
            self.method = get_component(self.path.method_name)
        except Exception as e:
            pass
        self.inputs = {}
        self.outputs = {}

    @reconstructor
    def after_load(self):
        self._load_fields()

    def prepare(self):
        """Load inputs and set parameters for flow from path info"""
        self.started_on = datetime.now()
        if self.path:
            self.origin = self.path.from_node
            self.destination = self.path.from_node

            # Loads inputs
            input_filters = self.order.get('inputs', {})
            for key, filters in input_filters.items():
                item = qry.get_item_by(location=self.origin,  **filters)
                self.inputs[key] = item

    def execute(self):
        """Execute method for generating outputs"""
        if self.method:
            self.method(self, self.controller)

    def terminate(self):
        """Commit the flow, consuming inputs and pushing outputs"""
        # Consume inputs
        if self.origin:
            for _input in self.inputs.values():
                if type(_input) is list:
                    for item in _input:
                        qty = self._get_qty(item, 'in')
                        item.consume(self, qty)

        # Produce outputs
        if self.destination:
            for output in self.outputs.values():
                if type(output) is list:
                    for item in output:
                        qty = self._get_qty(item, 'out')
                        item.produce(self, qty)
                else:
                    qty = self._get_qty(output)
                    output.produce(self, qty)

        self.finished_on = datetime.now()
        self.state = 'done'

    def _get_qty(self, item, inout):
        if hasattr(item, 'qty'):
            return item.qty
        elif self.path:   #  Gets information of qty from path
            item_flows = {'in': self.path.consumes,
                          'out': self.path.productions}
            for item_flow in item_flows[inout]:
                if item_flow.resource == item.resource:
                    return item_flow.qty

    def cancel(self):
        # No movements
        self.finished_on = datetime.now()
        self.state = 'cancelled'
