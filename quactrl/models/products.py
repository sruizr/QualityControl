from .graph import Item, Resource


class PartGroup:
    """Clasification of part models
    """
    def __init__(self, key, description, name=None):
        self.key = key
        self.name = name
        self.description = description
        self.part_models = []
        self.requirements = []


class PartModel(PartGroup):

    def __init__(self, part_number, description, name=None):
        self.key = part_number
        self.name = name
        self.description = description
        self.part_groups = []
        self.requirements = []

    def get_all_requirements(self):
        pass


class Requirement:
    """Requirement of PartModel, PartGroup or other requirements
    """
    def __init__(self, parent, characteristic, specs=None):
        self.parent = parent
        parent.requirements.append(self)
        self.key = '{}*{}'.format(parent.key, characteristic.key)

        self.characteristic = characteristic
        self.specs = specs if specs else {}


class Characteristic:
    """Attribute on an element
    """
    def __init__(self, attribute, element):
        self.key = '{}@{}'.format(attribute.key, element.key)
        self.attribute = attribute
        self.element = element
        self.failure_modes = {}


class Element:
    """Abstract subsystem or component
    """
    def __init__(self, key, name=None, parent=None):
        self.key = key
        self.name = name
        self.parent = parent
        if parent:
            self.parent.components = self

    def path(self):
        return '{}/{}'.format(self.parent.path(), self.key)
