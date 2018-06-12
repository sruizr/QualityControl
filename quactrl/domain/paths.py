from sqlalchemy.orm import synonym, reconstructor
from sqlalchemy.ext.hybrid import hybrid_property
from quactrl.domain.base import (Item, Resource, PathResource, Path, Node,
                                 Pars, Flow)
import quactrl.domain.flows as f


class ControlPlan(Path):
    __mapper_args__ = {'polymorphic_identity': 'control_plan'}

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
        self.validate_responsible(responsible)

        check = f.Check()

        check.part = test.part
        check.test = test
        check.tester = test.tester
        check.responsible = responsible

        return check
