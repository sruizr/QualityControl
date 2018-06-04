from tests.domain import SessionMockedTest
from tests import TestWithPatches
import quactrl.domain.paths as p
from unittest.mock import Mock



class A_ControlPlan(TestWithPatches):
    def setup_method(self, method):
        self.create_patches([
            'quactrl.domain.paths.Test',
            'quactrl.domain.paths.Path'
        ])

        self.control_plan = p.ControlPlan()

    def should_create_a_test_instance(self):
        in_part = Mock(name='part')
        responsible = Mock(name='responsible')

        test = self.control_plan.create_test(in_part, responsible)

        self.Test.assert_called_with()
        assert test == self.Test.return_value

    def should_check_responsible_when_new_test(self):
        pass

    def should_check_part_output_when_new_test(self):
        pass

    def should_open_checks_instances(self):
        pass
