import enum
from sqlalchemy.types import Enum, String
from sqlalchemy.orm import synonym
from quactrl.domain.data import (
    ForeignKey, relationship, backref, Column
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
        self.description = '{} @ {}'.format(
            self.atribute.description, self.element.description
            )


class FailureMode(Resource):
    __mapper_args__ = {'polymorphic_identity': 'failure_mode'}

    def __init__(self, **kwargs):
        pass

class Mode(Resource):
    __mapper_args__ = {'polymorphic_identity': 'mode'}



class PartModel(Resource):
    __mapper_args__ = {'polymorphic_identity': 'part_model'}



class DataAccessModule:
    """Operate with plan Entities"""
    pass
