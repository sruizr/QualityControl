import re
from quactrl.helpers import get_class
from quactrl.models.core import Resource
import quactrl.models.quality as qua
import logging


logger = logging.getLogger(__name__)


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
        self.groups = []

    def get_device_pars(self):
        if self.is_device():
            if not hasattr(self, '_device_pars'):
                device_class = self.pars.get('device_class')
                if device_class is not None:
                    device_pars = (get_class(device_class),
                                   self.pars.get('args', []),
                                   self.pars.get('kwargs', []))
                else:
                    for group in self.groups:
                        device_pars = group.get_device_pars()
                        if device_pars:
                            break
                self._device_pars = device_pars
            return self._device_pars

    def add_model(self, part_model):
        if part_model not in self.models:
            self.models.append(part_model)
            part_model.add_group(self)


    def is_device(self):
        if 'device_class' in self.pars:
            return True
        for group in self.groups:
            if group.is_device():
                return True
        return False


class PartModel(PartGroup):
    """Abstraction of part, type of part
    """
    def __init__(self, part_number, name=None, description=None, pars=None,
                 groups=None):
        super().__init__(part_number, name, description, pars)
        self.groups = [] if groups is None else groups


    def add_group(self, part_group):
        if part_group not in self.groups:
            self.groups.append(part_group)
            part_group.add_model(self)
        return self._Device

    def get_duec_content(self):
        return {
            'part_number': self.key,
            'part_name': self.name,
            'part_description': self.description
        }


class Part(qua.Subject):
    """Part with unique serial number
    """
    def __init__(self, model, serial_number, pars=None):
        super().__init__(resource=model, tracking=serial_number)
        self.model = model
        self.serial_number = serial_number
        self.pars = pars if pars else {}

    def get_duec_content(self):
        content = self.model.get_duec_content()
        content['serial_number'] = self.serial_number
        return content



class Requirement(Resource):
    """Requirement of PartModel, PartGroup or other requirements
    """
    def __init__(self, characteristic, key, specs=None):
        self.key = key
        self.characteristic = characteristic
        self.specs = specs if specs else {}

        self.requirements = []

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

    def get_requirement(self, filter_key):
        """Returns a subrequirement by a substring of key
        """
        for req in self.requirements:
            if filter_key in req.key:
                return req


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
