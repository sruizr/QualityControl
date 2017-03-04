class Batch:
    def __init__(self, part_number, batch_number, operator):
        self.part_number = part_number
        self.batch_number = batch_number
        self.operator = operator
        self.close_date = None
        self.items = {}


class Item:
    def __init__(self, serial_number):
        self.sn = serial_number
        self.status = None
        self.tests = []

    def validate(self, serial_number):
        pass

    @classmethod
    def has_passed_test(self, serial_number):
        return False


class Check:
    def __init__(self, control, item):
        self.control = control
        self.failures = []
        self.result = 'Pending'
        self.item = item

    def report_failure(self, failure):
        self.failures.append(failure)
        self.result = 'NOK'

    def end_check(self):
        if not self.failures:
            self.result = 'OK'


class Characteristic:
    def __init__(self, attribute, element):
        self.attribute = attribute
        self.element = element
        self.key = None

    def identify(self, key, specs=None):
        self.key = key
        if specs is not None:
            self.specs = specs

    def add_children(self, children):
        self.children = children

    @property
    def description(self):
        description = '{} en {}'.format(self.attribute, self.element)
        if self.key:
            description = description + ' - {}'.format(self.key)
        return description


class Control:
    def __init__(self, characteristic, method, pars=None):
        self.characteristic = characteristic
        self.method = method
        self.pars = pars


class Failure:
    def __init__(self, mode, attribute, element, key_element=None):
        self.failure_mode = mode
        self.attribute = attribute
        self.element = element
        self.key_element = key_element

    @property
    def description(self):
        description = '{} {} en {}'.format(self.failure_mode, self.attribute, self.element)
        if self.key_element:
            description = description + ' {}'.format(self.key_element)

        return description

    def __eq__(self, other):
        is_equal = self.failure_mode == other.failure_mode
        is_equal = is_equal and (self.attribute == other.attribute)
        is_equal = is_equal and (self.element == other.element)
        is_equal = is_equal and (self.key_element == other.key_element)

        return is_equal
