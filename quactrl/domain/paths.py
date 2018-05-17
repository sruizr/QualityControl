from enum import Enum
from sqlalchemy.orm import synonym, reconstructor
from threading import Thread, Event
from quactrl.domain.base import (Item, Resource, PathResource,
                                ItemRelation, Path, Node, Pars, Flow)
from datetime import datetime


class ControlPlan(Path):
    __mapper_args__ = {'polymorphic_identity': 'control_plan'}

    def __init__(self, name='Plan for testing 100% pars', method_name='quactrl.methods.by_pass', pars=None, **kwargs):
        super().__init__(**kwargs)
        self.method_name = method_name
        self.name = name
        if pars:
            self.pars = Pars(pars)

    @reconstructor
    def after_load(self):
        pass

    def create_flow(self, responsible, controller=None):
        return Test(self, responsible, controller)


class Control(Path):
    __mapper_args__ = {'polymorphic_identity': 'control'}

    characteristic = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @reconstructor
    def after_load(self):
        pass

    def add_characteristic(self, characteristic, **pars):

        path_resource = PathResource(self, characteristic, 'out', pars=pars)
        self.resource_list.append(path_resource)

    def create_flow(self, test, responsible):
        return Check(self, test, responsible, self.controller)

    def set_pars(self, pars):
        if self.pars:
            self.pars.set(pars)
        else:
            self.pars = Pars(pars)

    def get_pars(self):
        if self.pars:
            return self.pars.get()
#
