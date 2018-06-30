from sqlalchemy.orm import synonym, reconstructor
from sqlalchemy.ext.hybrid import hybrid_property
from quactrl.domain.base import (Item, Resource, PathResource, Path, Node,
                                 Pars, Flow)
import quactrl.domain.flows as f


class ControlPlan(Path):
    """Control plan for generating controls on parts or processes"""
    __mapper_args__ = {'polymorphic_identity': 'control_plan'}

    @property
    def part_model(self):
        return self.resources['part_model']

    @part_model.setter
    def part_model(self, part_model):
        self.resources['part_model'] = part_model

    @property
    def process(self):
        return self.resources['process']

    @process.setter
    def process(self, process):
        self.resources['process'] = process

    def create_flow(self, responsible, part):
        self.validate_responsible(responsible)
        self.validate_item(part)

        test = f.Test(
            path=self,
            responsible=responsible
        )
        test.part = part

        return test


class Control(Path):
    __mapper_args__ = {'polymorphic_identity': 'control'}

    def create_flow(self, test):
        """Create Check instance from test information"""
        responsible = test.responsible

        check = f.Check()

        check.part = test.part
        check.test = test
        check.tester = test.tester
        check.responsible = responsible

        return check


class Operation(Path):
    __mapper_args__ = {'polymorphic_identity': 'operation'}
    def create_flow(self, responsible):
        pass

class Reporting(Path):
    __mapper_args__ = {'polymorphic_identity': 'report'}

    @property
    def form(self):
        if 'form' in self.resources.keys():
            return self.resources['form']

    @form.setter
    def form(self, form):
        self.resources['form'] = form
