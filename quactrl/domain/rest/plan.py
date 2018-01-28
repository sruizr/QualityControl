import enum
from sqlalchemy.types import Enum
from sqlalchemy.orm import synonym
from quactrl.data import (
    Model, ForeignKey, relationship, backref, Column, String, Integer
)
from quactrl.domain.erp import Node, Path, Resource


class Process(Path):
    __mapper_args__ = {'polymorphic_identity': 'process'}


class Characteristic(Resource):
    __mapper_args__ = {'polymorphic_identity': 'characteristic'}

    def __init__(self, attribute, element):
        self.element = element
        self.attribute = attribute
        self.key = '{}_{}'.format(attibute.key, element.key)
        self.description =

        self.relations.append

    @element.setter
    def element(self, value):
        self.relations = Bob

class FailureMode(Resource):
    __mapper_args__ = {'polymorphic_identity': 'failure_mode'}

    def __init__(self, **kwargs):

class PartModel(Resource):
    __mapper_args__ = {'polymorphic_identity': 'part_model'}


class Control(Path):
    __mapper_args__ = {'polymorphic_identity': 'control'}

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


class DataAccessModule:
    """Operate with plan Entities""""
    pass
