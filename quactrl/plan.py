from quactrl import (
    Model, ForeignKey, relationship, backref, Column, String, Integer
)
from quactrl.resources import Element


class Characteristic(Model):
    __tablename__ = 'characteristics'

    attribute = Column(String)
    element_id = Column(Integer, ForeignKey('elements.id'), nullable=False)
    element = relationship(
        Element,
        backref=backref('characteristics', uselist=True, cascade='delete,all')
    )
    specs = Column(String)
    requirements = None

    def __init__(self, attribute, element, specs=None):
        self.attribute = attribute
        self.element = element
        if specs:
            self.specs = specs

    def __str__(self):
        description = '{} @ {}'.format(self.attribute, self.element)
        return description


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


class Control(Model):
    __tablename__ = 'controls'

    characteristic_id = Column(Integer, ForeignKey('characteristics.id'))
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


class Reaction(Model):
    __tablename__ = 'reactions'


class PlanDAO:
    """ Class to operate with Plan Objects"""
    pass
