import json
import importlib
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import reconstructor, remote
from sqlalchemy import ForeignKey, Column, Table
from sqlalchemy.types import (
    String, Integer, DateTime, Float
    )
from sqlalchemy.orm import relationship, backref, reconstructor, aliased
from quactrl.domain import Base, get_component, Abstract
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.associationproxy import association_proxy


class StockException(Exception):
    pass


class NotAuthorizedResponsible(Exception):
    pass


class MethodLoadError(Exception):
    """Method can not be loaded"""
    pass


class NoCompatibleItem(Exception):
    pass


class FlowAllocateException(Exception):
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


class Resource(Base, Abstract):
    __tablename__ = 'resource'

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


NodeLink = Table('node_link', Base.metadata,
                 Column('from_node_id', Integer, ForeignKey('node.id'),
                        primary_key=True),
                 Column('to_node_id', Integer, ForeignKey('node.id'),
                        primary_key=True))


class Node(Base, Abstract, WithPars):
    __tablename__ = 'node'

    id = Column(Integer, primary_key=True)
    key = Column(String(15), unique=True)
    name = Column(String(50))
    description = Column(String(250))

    def __init__(self, key,  **kwargs):
        self.key = key
        self.name = kwargs.pop('name', None)
        self.description = kwargs.pop('description', None)
        if kwargs:
            self.pars = Pars(**kwargs)

    # def add_item(self, item, qty=1.0, path=None, responsible=None):
    #     pass #TODO

    # def remove_item(self, item, qty=1.0, path=None, responsible=None):
    #     pass #TODO


class Item(Base, Abstract, WithPars):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)

    resource_id = Column(ForeignKey('resource.id'))
    tracking = Column(String(100), index=True)
    state = Column(String(100), index=True, default='active')

    resource = relationship("Resource")
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

    @property
    def total_qty(self):
        return sum([token.qty for token in self.avalaible_tokens])

    def produce(self, producer):
        """Produce a qty of item at producer destination"""
        qty = getattr(self, 'qty', 1.0)
        self.avalaible_tokens.append(
            Token(item=self, qty=qty, producer=producer, node=producer.destination)
        )

    def consume(self,consumer):
        """Cosume a qty of item at consumer origin"""
        qty = getattr(self, 'qty', None)
        origin = consumer.origin

        stocks = self.get_stocks()
        if origin not in stocks.keys():
            raise StockException('There is no stock on "{}"'.format(
                origin.key))

        avalaible_qty = sum([token.qty for token in stocks[origin]])
        if qty is not None and avalaible_qty < qty:
            raise StockException('qty {} is not avalaible at {}'.format(
                qty,
                origin.key
            ))


        if qty is None:
            for token in stocks[origin]:
                token.consume(consumer)
        else:
            for token in stocks[origin]:
                if qty == 0:
                    break
                if qty >= token.qty:
                    token.consume(consumer)
                    qty -= token.qty
                else:
                    token.consume(consumer, qty)
                    qty = 0


ItemLink = Table('item_link', Base.metadata,
                 Column('from_item_id', Integer, ForeignKey('item.id')),
                 Column('to_item_id', Integer, ForeignKey('item.id')))


class Path(Abstract, Base, WithPars):
    __tablename__ = 'path'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('path.id'), index=True)
    from_node_id = Column(Integer, ForeignKey('node.id'), index=True)
    to_node_id = Column(Integer, ForeignKey('node.id'), index=True)
    role_id = Column(Integer, ForeignKey('node.id'))

    sequence = Column(Integer, default=0)
    created_on = Column(DateTime, default=datetime.now)
    removed_on = Column(DateTime)
    method_name = Column(String(100))

    from_node = relationship('Node', foreign_keys=[from_node_id])
    to_node = relationship('Node', foreign_keys=[to_node_id])
    role = relationship('Node', foreign_keys=[role_id])
    steps = relationship('Path',
                         backref=backref('parent', remote_side=[id]),
                         order_by='Path.sequence')

    resources = association_proxy(
        'path_resource', 'resource',
        creator=lambda k, v: PathResource(key=k, resource=v)
    )

    def create_flow(self, responsible):
        raise NotImplementedError()

    def validate_responsible(self, responsible):
        # Check responsible has role
        if self.role not in responsible.roles:
            raise NotAuthorizedResponsible(
                'Responsible {} is not autorized to implement path'.format(
                    responsible.name
                )
            )

    def validate_item(self, item):
        if (item.resource not in self.resources.values()):
            for resource in self.resources.values():
                if resource in item.resource.groups:
                    return

            raise NoCompatibleItem(
                'Item of resource {} is not compatible with path'.format(
                    item.resource.name
                )
            )


class PathResource(Base):
    __tablename__ = 'path_resource'

    id = Column(Integer, primary_key=True)
    path_id = Column(Integer, ForeignKey('path.id'), index=True)
    resource_id = Column(Integer, ForeignKey('resource.id'))

    key = Column(String(10), nullable=False)
    resource = relationship('Resource')
    path = relationship('Path', backref=backref(
        'path_resource',
        collection_class=attribute_mapped_collection('key')
    ))


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

    producer = relationship('Flow', foreign_keys=[producer_id], backref='production')
    consumer = relationship('Flow', foreign_keys=[consumer_id], backref='consum')

    def consume(self, consumer, qty=None):
        if qty is not None:
            if qty > self.qty:
                raise StockException('Quanty avalible is less than consume request')
            elif qty < self.qty:
                rest = self.qty - qty

                self.item.avalaible_tokens.append(
                    Token(qty=rest, producer=self.producer, node=self.node)
                )
                self.qty = qty

        self.consumer = consumer

    def is_consumed(self):
        return self.consumer is not None


class Flow(Abstract, Base):
    __tablename__ = 'flow'

    id = Column(Integer, primary_key=True)
    path_id = Column(Integer, ForeignKey('path.id'))
    responsible_id = Column(Integer, ForeignKey('node.id'), index=True)
    parent_id = Column(Integer, ForeignKey('flow.id'), index=True)

    started_on = Column(DateTime)
    finished_on = Column(DateTime)
    state = Column(String(15), default='open')
    tracking = Column(String(100))

    path = relationship('Path')
    responsible = relationship('Node')

    operations = relationship('Flow',
                              backref=backref('parent', remote_side=[id]),
                              order_by='Flow.id')

    def start(self, **kwargs):
        """Create internal fields for assuring the flow of items"""
        self.destination = self.origin = None
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.inputs = []
        self.outputs = []

        self.started_on = datetime.now()
        self.state = 'started'

    def execute(self):
        """Basic flow execution, to be overwritten"""
        if self.path:
            self.path.method(self)

    def finish(self):
        """Marks finish and result"""
        if self.state in ('started', 'ongoing'):
            self.state = 'finished'
        self.finished_on = datetime.now()

    def run(self, **kwargs):
        """Simple flow running"""
        self.start(**kwargs)

        for operation in self.op_creator():
            if self.state == 'cancelled':
                break
            operation.run()

        self.execute()
        self.finish()
        self.close()

    def op_creator(self):
        for step in self.path.steps:
            operation = step.create_flow()
            operation.responsible = self.responsible
            self.operations.append(operation)
            yield operation

    def close(self):
        self.allocate()
        self.throw()

    def throw(self):
        """Consume inputs and subinputs and produce outputs and suboutputs"""

        # Consume inputs
        if self.origin:
            for _input in self.inputs:
                _input.consume(self)

        # Produce outputs
        if self.destination:
            for output in self.outputs:
                output.produce(self)

        # Move items from operations
        for operation in self.operations:
            operation.throw()

    def allocate(self):
        """Define origins and destinations from path information and final state"""
        if self.finished_on is None:
            raise FlowAllocateException('Check is not properly finished')

        if self.origin is None and self.path:
            self.origin = self.path.from_node
            if self.origin is None and self.path.parent:
                self.origin = self.path.parent.from_node

        if self.state == 'cancelled':
            self.destination = self.origin
            for operation in self.operations:
                operation.state = 'cancelled'
        else:
            if self.destination is None and self.path:
                self.destination = self.path.to_node
                if self.destination is None and self.path.parent:
                    self.destination = self.path.parent.to_node

        for operation in self.operations:
            operation.allocate()

    def cancel(self):
        """Returns to origin movement of items, outputs returned to origin"""
        self.finished_on = datetime.now()
        self.state = 'cancelled'
