from tests.domain import EmptyDataTest
from tests import TestWithPatches
import quactrl.domain.paths as p
import quactrl.domain.resources as r
import quactrl.domain.items as i
import quactrl.domain.nodes as n
import quactrl.domain.flows as f
from unittest.mock import Mock


class A_ControlPlan:
    def should_create_a_test_instance(self):
        control_plan = p.ControlPlan()
        control_plan.validate_item = Mock()
        control_plan.validate_responsible = Mock()

        responsible = n.Person()
        part = i.Part()

        test = control_plan.create_flow(responsible, part)

        assert control_plan.validate_item.called
        assert control_plan.validate_responsible.called
        assert type(test) is f.Test
        assert test.part == part
        assert test.responsible == responsible


class A_Control(EmptyDataTest):
    def should_create_a_check_instance(self):
        control = p.Control()
        test = f.Test()
        test.part = Mock()
        test.tester = Mock()

        responsible = n.Person()
        test.responsible = responsible

        check = control.create_flow(test)

        assert type(check) is f.Check
        assert check.part == test.part
        assert check.tester == test.tester
        assert check.test == test
        assert check.responsible == responsible
