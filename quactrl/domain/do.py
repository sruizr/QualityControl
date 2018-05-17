import importlib
import json
import os
from sqlalchemy.orm import synonym, reconstructor, aliased
from quactrl.domain.base import Item, Resource, Node, NodeRelation, Pars, Flow, Token
from quactrl.domain.plan import PartModel, Operation, DeviceModel
from quactrl.domain import get_component
from quactrl.domain.base import Path



class DataAccessModule:
    _devices = {}
    _duts = {}

    def __init__(self, dal):
        self.dal = dal
        self._duts = {}
        self.session = None
