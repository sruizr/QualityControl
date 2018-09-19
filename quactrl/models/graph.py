from . import Entity
import datetime


class Node(Entity):
    """Place of tokens
    """
    def __init__(self, key, name=None, description=None):
        self.key = key
        self.name = name
        self.description = None


class Resource(Entity):
    """Types of tokens
    """
    def __init__(self, key, name=None, description=None):
        self.key = key
        self.name = name
        self.description = description


class Item(Entity):
    """Instance of resource on graph, it can be divided
    """
    def __init__(self, resource, tracking=None):
        self.resource = resource
        self.tracking = tracking
        self.state = 'open'
        self.tokens = []


class Token:
    """Parts of items on nodes
    """
    def __init__(self, item, producer, qty):
        self.item = item
        self.node = producer.path.to_node
        self.producer = producer
        self.qty = qty

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
