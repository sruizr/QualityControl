from . import Entity


class Node(Entity):
    """Place of tokens
    """
    pass


class Resource(Entity):
    """Types of tokens
    """
    pass


class Item(Entity):
    """Token wich flows from one node to other
    """
    pass


class Path(Entity):
    """Planned flow from one node to other
    """
    pass


class Flow(Entity):
    """Movement of token from one node to other
    """
    pass
