from . import Entity
import datetime


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


class Item:
    """Instance of resource
    """
    def __init__(self, resource, tracking, parent=None, **kwargs):
        self.resource = resource
        self.tracking = tracking
        self.pars = kwargs
        self.tokens = []
        self.parent = parent
        if parent:
            self.parent.components.append(self)
        self.components = []

    def __setattr__(self, key, value):
        if key in self.pars.keys():
            self.pars[key] = value
        else:
            self.__dict__[key] = value

    def __getattr__(self, key):
        if key in self.pars.keys():
            return self.pars[key]

    def get_stocks(self):
        """Group avalaible tokens by nodes"""
        stocks = {}
        for token in self.tokens:
            if token.node in stocks.keys():
                stocks[token.node].append(token)
            else:
                stocks[token.node] = [token]

        return stocks

    @property
    def total_qty(self):
        return sum([token.qty for token in self.tokens if token.producer is None])

    def produce(self, producer):
        """Produce a qty of item at producer destination"""
        qty = getattr(self, 'qty', 1.0)
        self.avalaible_tokens.append(
            Token(item=self, qty=qty, producer=producer, node=producer.destination)
        )

    def consume(self, consumer):
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

# class Path(Abstract, Base, WithPars):
#     __tablename__ = 'path'

#     id = Column(Integer, primary_key=True)
#     parent_id = Column(Integer, ForeignKey('path.id'), index=True)
#     from_node_id = Column(Integer, ForeignKey('node.id'), index=True)
#     to_node_id = Column(Integer, ForeignKey('node.id'), index=True)
#     role_id = Column(Integer, ForeignKey('node.id'))

#     sequence = Column(Integer, default=0)
#     created_on = Column(DateTime, default=datetime.now)
#     removed_on = Column(DateTime)
#     method_name = Column(String(100))

#     from_node = relationship('Node', foreign_keys=[from_node_id])
#     to_node = relationship('Node', foreign_keys=[to_node_id])
#     role = relationship('Node', foreign_keys=[role_id])
#     steps = relationship('Path',
#                          backref=backref('parent', remote_side=[id]),
#                          order_by='Path.sequence')

#     resources = association_proxy(
#         'path_resource', 'resource',
#         creator=lambda k, v: PathResource(key=k, resource=v)
#     )

#     def create_flow(self, responsible):
#         raise NotImplementedError()

#     def validate_responsible(self, responsible):
#         # Check responsible has role
#         if self.role not in responsible.roles:
#             raise NotAuthorizedResponsible(
#                 'Responsible {} is not autorized to implement path'.format(
#                     responsible.name
#                 )
#             )

#     def validate_item(self, item):
#         if (item.resource not in self.resources.values()):
#             for resource in self.resources.values():
#                 if resource in item.resource.groups:
#                     return

#             raise NoCompatibleItem(
#                 'Item of resource {} is not compatible with path'.format(
#                     item.resource.name
#                 )
#             )

#     def validate_resource(self, resource):
#         if resource in self.resources.values():
#             return True
#         else:
#             for group in resource.groups:
#                 if group in self.resources.values():
#                     return True

#         return False


# class PathResource(Base):
#     __tablename__ = 'path_resource'

#     path_id = Column(Integer, ForeignKey('path.id'), index=True, primary_key=True)
#     key = Column(String(10), nullable=False, primary_key=True)
#     resource_id = Column(Integer, ForeignKey('resource.id'))

#     resource = relationship('Resource')
#     path = relationship('Path', backref=backref(
#         'path_resource',
#         collection_class=attribute_mapped_collection('key')
#     ))



class Flow(Abstract, Base):
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


class Node(Entity):
    """Place of tokens
    """
    def __init__(self, key, name=None, description=None, parent=None):
        self.key = key
        self.name = name
        self.description = None
        self.parent = parent
        self.nodes = []
        if parent:
            parent.nodes.append(self)

    def to_dict(self, level):
        result = []
        return result

class Resource(Entity):
    """Types of tokens
    """
    def __init__(self, key, name=None, description=None):
        self.key = key
        self.name = name
        self.description = description

    def to_dict(self, level):
        return {
            'key': self.key,
            'name': self.name,
            'description': self.description
        }


class Token:
    """Parts of items on nodes
    """
    def __init__(self, item, qty, node, producer):
        self.item = item
        self.item.tokens.append(self)
        self.node = node
        self.producer = producer
        self.qty = qty
        self.consumer = None

    def consume(self, consumer, qty=None):
        """Consume a qty of the token,
        if qty is None, all token qty
        """
        if qty is not None:
            if qty > self.qty:
                raise Exception('Quantity avalible is less than consume request')
            elif qty < self.qty:
                rest = self.qty - qty

                self.item.avalaible_tokens.append(
                    Token(qty=rest, producer=self.producer, node=self.node)
                )
                self.qty = qty

        self.consumer = consumer

        @property
        def is_consumed(self):
            return self.consumer is not None


class Path(Entity):
    """Planned flow from one node to other
    """
    def __init__(self, from_node, to_node, role=None, method_name=None, parent=None, sequence=0):
        self.created_on = datetime.datetime.now()
        self.removed_on = None

        self.from_node = from_node
        self.to_node = to_node
        self.role = role
        self.method_name = method_name
        self.resources = []

    def create_flow(self, responsible):
        pass

    def validate_responsible(self, responsible):
        pass

    def validate_resource(self, resource):
        pass

    def validate_item(self, item):
        pass


class Flow(Entity):
    """Movement of token from one node to other
    """
    def __init__(self, path, tracking=None, responsible=None):
        self.started_on = datetime.datetime.now()
        self.finished_on = None

        self.path = path
        self.tracking = tracking
        self.responsible = responsible
        self.state = 'open'
        self.flows = []

    def begin(self, **kwargs):
        self.destination = self.origin = None
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.inputs = []
        self.outputs = []

        self.started_on = datetime.now()
        self.state = 'started'

    def execute(self):
        if self.path:
            self.path.method(self)

    def finish(self):
        if self.state in ('started', 'ongoing'):
            self.state = 'finished'
        self.finished_on = datetime.now()

        self._allocate_nodes()
        self._process_tokens()

    def run(self, **kwargs):
        """Quick flow running
        """
        self.start(**kwargs)

        for operation in self.op_creator():
            if self.state == 'cancelled':
                break
            operation.run()

        self.execute()
        self.finish()

    def _allocate_nodes(self):
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
        pass
