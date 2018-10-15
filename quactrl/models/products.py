import re


class PartGroup:
    """Clasification of part models
    """
    def __init__(self, key, description, name=None):
        self.key = key
        self.name = name
        self.description = description
        self.part_models = []
        self.requirements = {}


class PartModel(PartGroup):
    """Abstraction of part, type of part
    """
    def __init__(self, part_number, description, name=None):
        self.key = part_number
        self.name = name
        self.description = description
        self.part_groups = []
        self.requirements = {}


class Requirement:
    """Requirement of PartModel, PartGroup or other requirements
    """
    def __init__(self, characteristic, key, specs=None):
        self.key = key
        self.characteristic = characteristic
        self.specs = specs if specs else {}
        self.requirements = {}

    @property
    def eid(self):
        return re.findall('.*>(.*)', self.key)[0]


class Characteristic:
    """Attribute on an element
    """
    def __init__(self, attribute, element, key=None):
        self.key = '{}@{}'.format(attribute.key, element.key) \
            if key is None else key
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


class  Attribute:
    """Evaluable attribute of an element
    """
    def __init__(self, key, name, description=None):
        self.key = key
        self.name = name
        self.description = description
