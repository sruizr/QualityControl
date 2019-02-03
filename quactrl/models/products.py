import re
from quactrl.helpers import get_class
from quactrl.models.core import Resource
import quactrl.models.quality as qua


class PartGroup(Resource):
    """Clasification of part models
    """
    def __init__(self, key, name, description=None,
                 pars=None):
        self.key = key
        self.name = name
        self.description = description
        self.pars = pars if pars else {}

        self.models = []
        self.requirements = {}

    @property
    def Device(self):
        if not hasattr(self, '_Device'):
            device_class = self.pars.get('device_class')
            self._Device = None
            if device_class is not None:
                self._Device = get_class(device_class) if device_class else None
                self.kwargs = self.pars.get('kwargs', {})
        return self._Device

    def add_model(self, part_model):
        if part_model not in self.models:
            self.models.append(part_model)
            part_model.add_group(self)


class PartModel(PartGroup):
    """Abstraction of part, type of part
    """
    def __init__(self, part_number, name=None, description=None, pars=None):
        super().__init__(part_number, name, description, pars)
        self.groups = []

    def add_group(self, part_group):
        if part_group not in self.groups:
            self.groups.append(part_group)
            part_group.add_model(self)

    @property
    def Device(self):
        if not hasattr(self, '_Device'):
            device_class = self.pars.get('device_class')
            if device_class is None:
                self._Device, self.kwargs = self._find_Device()
            else:
                self._Device = get_class(device_class)
                self.kwargs = self.pars.get('kwargs', {})

        return self._Device

    def _find_Device(self):
        for group in self.groups:
            if group.Device:
                return group.Device, group.kwargs.copy()
        return None, None

    def create_dut(self, connection):
        """Return a device instance if part model is a device
        """
        if self.Device:
            return self.Device(connection, **self.kwargs)

    def is_device(self):
        return self.Device is not None


class Part(qua.Subject):
    """Part with unique serial number
    """
    def __init__(self, model, serial_number, pars=None):
        self.model = model
        self.serial_number = serial_number
        self.pars = pars if pars else {}

        self.dut = None

    def set_dut(self, connection):
        self.dut = self.model.create_dut(connection)


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

    def add_requi(self, requirement):
        self.requirements[requirement.key] = requirement


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

    def add_failure_mode(self, mode):
        failure_mode = qua.FailureMode(self, mode)
        self.failure_modes[failure_mode.mode.key] = failure_mode


class Element(Resource):
    """Abstract subsystem or component
    """
    def __init__(self, key, name=None, description=None, parent=None):
        self.key = key
        self.name = name if name else key
        self.description = description

        self.parent = parent
        if parent:
            self.parent.components = self

    def path(self):
        return '{}/{}'.format(self.parent.path(), self.key)


class Attribute(Resource):
    """Evaluable attribute of an element
    """
    def __init__(self, key, name=None, description=None):
        self.key = key
        self.name = name if name else key
        self.description = description
