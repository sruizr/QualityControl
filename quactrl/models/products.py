import re
from quactrl.helpers import get_class
from quactrl.models.core import Resource


class PartGroup(Resource):
    """Clasification of part models
    """
    def __init__(self, key, name, description=None,
                 pars=None):
        self.key = key
        self.name = name
        self.description = description
        self.pars = pars if pars else {}

        self.kwargs = self.pars.get('kwargs', {})
        device_class = self.pars.get('device_class')
        self.Device = get_class(device_class) if device_class else None

        self.part_models = []
        self.requirements = {}

    def add_model(self, part_model):
        self.part_models.append(part_model)
        if self not in part_model.part_groups:
            part_model.add_group(self)


class PartModel(PartGroup):
    """Abstraction of part, type of part
    """
    def __init__(self, part_number, name=None, description=None, pars=None):
        super().__init__(part_number, name, description, pars)
        self.part_groups = []

    def _find_Device(self):
        for group in self.part_groups:
            if group.Device:
                return group.Device, group.kwargs.copy()
        return None, None

    def create_dut(self, connection):
        """Return a device instance if part model is a device
        """
        if self.Device:
            return self.Device(connection, self.kwargs)
        else:
            Device, kwargs = self._find_Device()
            if Device:
                kwargs.update(self.kwargs)
                return Device(connection, **kwargs)

    def is_device(self):
        if self.Device:
            return True
        else:
            Device, kwargs = self._find_Device()
            return Device is not None

    def add_group(self, group):
        self.part_groups.append(group)
        if self not in group.part_models:
            group.add_model(self)


class Requirement(Resource):
    """Requirement of PartModel, PartGroup or other requirements
    """
    def __init__(self, characteristic, key, specs=None):
        self.key = key
        self.characteristic = characteristic
        self.specs = specs if specs else {}
        self.requirements = {}

    @property
    def eid(self):
        result = re.findall('.*>(.*)', self.key)
        return result[0] if result else ''

    @property
    def description(self):
        char = self.characteristic
        value = '{} [{}]'.format(char.description,
                                 self.eid)
        return value


class Characteristic(Resource):
    """Attribute on an element
    """
    def __init__(self, attribute, element, key=None):
        self.key = '{}@{}'.format(attribute.key, element.key) \
            if key is None else key
        self.attribute = attribute
        self.element = element
        self.failure_modes = {}

    def __str__(self):
        return '{} @ {}'.format(self.attribute.name, self.element.name)

    @property
    def description(self):
        return str(self)


class Element(Resource):
    """Abstract subsystem or component
    """
    def __init__(self, key, name, description=None, parent=None):
        self.key = key
        self.name = name
        self.description = description

        self.parent = parent
        if parent:
            self.parent.components = self

    def path(self):
        return '{}/{}'.format(self.parent.path(), self.key)


class Attribute(Resource):
    """Evaluable attribute of an element
    """
    def __init__(self, key, name, description=None):
        self.key = key
        self.name = name
        self.description = description
