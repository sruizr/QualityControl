from unittest.mock import Mock, patch
from quactrl.services.inspection import (
    InspectionManager, Inspector, ControlRunner, SampleController)
import pytest

current = pytest.mark.current


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
        self.im = InspectionManager(environment)


    @current
    def should_setup_session(self):
        process = Mock()

        self.im.setup_session(process)

        assert self.im.process == process
        assert self.im.device_repo
        self.im.env.session.DeviceRepository.assert_called_once_with(self.im.process)

    @current
    def should_setup_batch(self):
        batch = Mock()
        batch.partnumber = '12345'
        im = self.im

        im.process = Mock()
        im.setup_batch(batch)
        self.im.setup_batch(batch)

        assert self.im.batch
        assert len(self.im.inspectors) == 3

    def should_create_one_inspector_by_branch(self):
        self.im.controls = create_fake_control_struct()
        self.im.create_inspectors()


        assert len(self.im.inspectors) == 3

    def should_manage_serial_inspectors(self):
        pass

    def should_manage_paralel_inspectors(self):
        pass

    def should_start_inspectors(self):
        pass

    def should_stop_inspectors(self):
        pass

    def should_react_when_failures(self):
        pass


class An_Inspector:
    def setup(self, method):
        pass

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
