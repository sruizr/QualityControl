from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from quactrl import Model


class Characteristic(Model):
    __tablename__ = 'characteristics'

    id = Column(Integer, primary_key=True)
    attribute = Column(String)
    element_id = Column(Integer)
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


class Control(Model):
    __tablename__ = 'controls'

    characteristic_id = Column(Integer)
    sampling = Column(Integer)
    method_id = Column(Integer)
    parent_id = Column(Integer)
    detection_point_id = Column(Integer)
    measure_system_id = Column(Integer)

    reaction_id = Column(Integer)

    def __init__(self, characteristic, method, pars=None):
        self.characteristic = characteristic
        self.method = method
        self.pars = pars


class Method(Model):
    __tablename__ = 'methods'
    name = Column(String)
    content = Column(String)


class FailureMode(Model):
    __tablename__ = 'failures'

    mode = Column(String(30))
    characteristic_id = Column(Integer)
    characteristic = 'f'

    def __init__(self, characteristic, mode):
        self.characteristic = characteristic
        self.mode = mode

    def __str__(self):
        description = '{} {}'.format(self.mode, self.characteristic)

        return description


class Reaction(Model):
    __tablename__ = 'reactions'


class PlanDAO:
    """ Class to operate with Plan Objects"""
    pass
