from unittest.mock import Mock, patch
from quactrl.services.inspection import (
    InspectionManager, Inspector, ControlRunner, SampleController)
import pytest

current = pytest.mark.current


class FakeEnvironment:
    def __init__(self):
        self.env = Mock()

def create_fake_control_struct():
    def get_branch(length):
        branch = [Mock() for _ in range(length)]
        for index, control in enumerate(branch):
            control.prev = branch[index - 1]
        branch[0].prev = None
        return branch

    control_branch_1 = get_branch(2)
    control_branch_2 = get_branch(3)
    control_branch_3 = get_branch(4)

    # one branch with two branches
    control_branch_2[0].prev = control_branch_3[0].prev = control_branch_1[-1]
    control_branch_1.extend(control_branch_2)
    control_branch_1.extend(control_branch_3)

    return control_branch_1


class FakeControl:
    pass


class FakeCharacteristic:
    pass


class An_InspectionManager:
    def setup_method(self, method):
        environment = Mock()
        environment.process = Mock()
        Control = Mock()
        Control.collect.return_value = create_fake_control_struct()


class An_Inspector:
    def setup_method(self, method):
        self.service = Mock()
        self.env = self.service.env
        self.inspector = Inspector(self.service)

    def should_create_control_runners(self):
        pass

    def should_run_controls(self):
        pass

    def should_stop_controls(self):
        pass

    def should_report_checking_status_to_observers(self):
        pass

    def should_persist_results(self):
        pass

    def should_create_inspection_record(self):
        pass

    def should_update_check_records(self):
        pass

    def should_notify_ending_to_mng(self):
        pass

    @pytest.mark.ahora
    def should_execute_methods(self):
        check = Mock()
        check.control = Mock()
        check.control.method_name = 'method_name'

        method = self.env.method_repo.get.return_value
        session = self.env.session
        view = self.env.view
        service = self.service

        # Return failures
        self.inspector.run_check(check)

        method.assert_called_once_with(self.inspector, check)
        view.starting.assert_called_once_with(check)
        assert not view.finished.called
        check.add_failures.assert_called_with(method.return_value)
        session.add.assert_called_with(check)

        # No failures
        method.return_value = []
        self.inspector.run_check(check)
        view.finished.assert_called_with(check)

    @pytest.mark.ahora
    def should_eval_value(self):
        characteristic = Mock()
        characteristic.limits = [-1, 1]
        modes = ['very low', 'very high', 'a bit suspicious']
        uncertainty = 0.2

        value = 0
        failure_mode = self.inspector.eval_value(value, characteristic, uncertainty, modes)
        assert failure_mode is None

        value = 0.81
        failure_mode = self.inspector.eval_value(value, characteristic, uncertainty, modes)
        self.env.repo_fry.get.return_value.get.assert_called_with('a bit suspicious very high', characteristic)

        value = 1.1
        failure_mode = self.inspector.eval_value(value, characteristic, uncertainty, modes)
        self.env.repo_fry.get.return_value.get.assert_called_with('very high', characteristic)

        value = -0.81
        failure_mode = self.inspector.eval_value(value, characteristic, uncertainty, modes)
        self.env.repo_fry.get.return_value.get.assert_called_with('a bit suspicious very low', characteristic)

        value = -1.1
        failure_mode = self.inspector.eval_value(value, characteristic, uncertainty, modes)
        self.env.repo_fry.get.return_value.get.assert_called_with('very low', characteristic)


class A_ControlRunner:

    def setup(self, method):
        pass

    def should_create_suitable_sample_controller(self):
        pass

    def should_execute_methods(self):
        pass

    def should_report_check_to_inspector(self):
        pass


class A_SampleController:

    def setup(self, method):
        pass

    def should_persist_control_counters(self):
        pass

    def should_notify_control_runner(self):
        pass

    def should_count_time(self):
        pass

    def should_count_units(self):
        pass
