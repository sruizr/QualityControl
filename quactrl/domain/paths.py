from enum import Enum
from sqlalchemy.orm import synonym, reconstructor
from threading import Thread, Event
from quactrl.domain.base import (Item, Resource, PathResource,
                                ItemRelation, Path, Node, Pars, Flow)
import quactrl.domain.flows as f
from datetime import datetime



class NotAutorizedResponsible(Exception):
    # duplicated!!
    pass


class IncorrectOutResource(Exception):
    pass


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

    def create_flow(self, in_part, responsible):
        if self.role not in responsible.roles:
            raise NotAutorizedResponsible(
                'Responsible {} can not access to the flow'.format(
                    responsible.name)
            )

        if in_part.resource not in self.resources.values():
            raise IncorrectOutResource(
                'Resource {} is not allowed for the current control plan'.format(
                    in_part.resource.name)
            )

        test = f.Test(self, in_part, responsible)
        for step in self.steps:
            test.steps.append(step.create_flow())

        return test


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
        return f.Check(self, test, responsible, self.controller)

    def set_pars(self, pars):
        if self.pars:
            self.pars.set(pars)
        else:
            self.pars = Pars(pars)

    def get_pars(self):
        if self.pars:
            return self.pars.get()
#
