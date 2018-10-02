from .graph import Item, Resource


class Part(Batch):
    """Part with unique serial number
    """
    def __init__(self, model, tracking, location=None):
        super().__init__(qty=1, **kwargs)


class PartModel(PartGroup):
    pass


class PartGroup:
    """Clasification of part models
    """
    def __init__(self, key, description, name=None):
        self.key = key
        self.description = description
        self.name = name if name else key


class Batch:
    """Result of an operation action
    """
    def __init__(self, model, tracking, qty):
        self.model = model
        self.tracking = tracking
        self.qty = qty
