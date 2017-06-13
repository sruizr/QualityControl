import enum
from sqlalchemy.types import Enum
from quactrl import (
    Model, ForeignKey, relationship, backref, Column, String, Integer
)
from quactrl.resources import Element, Operation, Device


class Characteristic(Model):
    __tablename__ = 'characteristic'

    attribute = Column(String)
    element_id = Column(Integer, ForeignKey('elements.id'), nullable=False)
    element = relationship(
        Element,
        backref=backref('characteristics', uselist=False, cascade='delete,all')
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


class CharacteristicRelation(Model):
    __tablename__ = 'char_relations'
    from_char_id = Column(Integer)

    to_char_id =1

    def __init__(self, requirem):
        pass


class FailureMode(Model):
    __tablename__ = 'failure_mode'

    mode = Column(String(30))
    characteristic_id = Column(Integer, ForeignKey('characteristic.id'))
    characteristic = relationship('Characteristic')

    def __init__(self, characteristic, mode):
        self.characteristic = characteristic
        self.mode = mode

    def __str__(self):
        description = '{} {}'.format(self.mode, self.characteristic)

        return description


class Method(Model):
    __tablename__ = 'methods'
    number = Column(String(15))
    name = Column(String(150))
    content = Column(String)

    def __init__(self, number, name=None, content=None):
        self.number = number
        self.name = name
        self.content = content


class Reaction(enum.Enum):
    none_level = 0
    low_level = 1
    critical_level = 2
    security_level = 3


class Sampling(enum.Enum):
    ongoing = 0
    every_unit = 1

    each_10 = 21
    each_100 = 22
    each_1000 = 23
    each_10000 = 24
    each_100000 = 25

    by_second = 30
    by_minute = 31
    by_hour = 32
    by_day = 33
    by_week = 34
    by_month = 35
    by_year = 36


class Control(Model):
    __tablename__ = 'controls'

    characteristic_id = Column(Integer, ForeignKey('characteristic.id'))
    characteristic = relationship(Characteristic)

    sampling_qty = Column(Integer, default=1)
    sampling_class = Column(Enum(Sampling))

    detection_point_id = Column(Integer, ForeignKey('operations.id'))
    detection_point = relationship(Operation)

    method_id = Column(Integer, ForeignKey('methods.id'))
    method = relationship(Method)
    method_details = Column(String(200))

    measure_system_id = Column(Integer, ForeignKey('devices.id'))
    measure_system = relationship(Device)

    reaction = Column(Enum(Reaction))

    def __init__(self, characteristic, sampling_class,
                 method, detection_point, sampling_qty=1, method_details=None,
                 reaction=Reaction.low_level):

        self.characteristic = characteristic
        self.sampling_class = sampling_class
        self.method = method
        self.detection_point = detection_point

        self.sampling_qty = sampling_qty
        self.method_details = method_details
        self.reaction = reaction


class PlanDAO:
    """ Class to operate with Plan Objects"""
    pass
