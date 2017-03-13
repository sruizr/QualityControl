from sqlalchemy import Column, String, Integer
from quactrl import Base


class Characteristic(Base):
    __tablename__ = 'characteristics'

    id = Column(Integer, primary_key=True)
    attribute = Column(String)
    element = Column(String)
    element_key = Column(String)
    specs = Column(String)

    def __init__(self, attribute, element, element_key):
        self.attribute = attribute
        self.element = element
        self.element_key = element_key

    def identify(self, key, specs=None):
        self.element_key = key
        if specs is not None:
            self.specs = specs

    def add_children(self, children):
        self.children = children

    def __repr__(self):
        description = '{} en {}'.format(self.attribute, self.element)
        if self.element_key:
            description = description + ' - {}'.format(self.element_key)
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
