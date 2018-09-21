import graph



class Person(graph.Node):
    pass


class Device(graph.Token):
    """Device from a location to be used for operations
    """
    pass


class Location(graph.Node):
    """Site of products
    """
    pass


class PartModel(graph.Resource):
    pass


class PartGroup(graph.Resource):
    """Clasification of part models
    """
    pass


class Batch(graph.Item):
    """Result of an operation action
    """
    pass


class Route(graph.Path):
    """Planning of an operation on parts
    """
    def __init__(self, inputs, outputs, source, destination):
        self.steps = []


class Part(Batch):
    """Part with unique serial number
    """
    def __init__(self, **kwargs):
        super().__init__(qty=1, **kwargs)


class Operation(graph.Flow):
    """Add value stream action over a batch
    """
    def __init__(self, route, batch, responsible):
        pass


class Action(graph.Flow):
    """Execution of an step on a route
    """
    def __init__(self, operation, step):
        super().__init__(step, operation)
