from unittest.mock import Mock, patch
from quactrl.services.inspection import (
    InspectionManager, Inspector, ControlRunner, SampleController)


def create_fake_control_struct():
    def get_branch(length):
        branch = [Mock() for _ in range(length)]
        for index, control in enumerate(branch):
            control.prev = control[index - 1]
        branch[0].prev = None

    control_branch_1 = get_branc(2)
    control_branch_2 = get_branch(3)
    control_branch_3 = get_branch(4)

    # one branch with two branches
    control_branch_2[0].prev = control_branch_3[0].prev = control_branch_1[-1]
    control_branch_1.extend(control_branch_2).extend(control_branch_3)

    return control_branch_1


class FakeControl:
    pass


class FakeCharacteristic:
    pass


class An_InspectionManager:
    def setup(self, method):
        environment = Mock()
        environment.process = Mock()
        Control = Mock()
        Control.collect.return_value = create_fake_control_struct()
        self.inspection_manager = InspectionManager(environment)
        self.inspection_manager

    def should_setup_session(self):
        process = Mock()
        self.inspection_manager.load_devices = Mock()
        self.inspection_manage.setup_session(process)

        assert self.inspection_manager.process == process
        self.inspection_manager.load_devices.assert_called_once_with(process)

    def should_setup_batch(self):
        batch = Mock()
        self.inspection_manager.load_controls = Mock()

        self.inspection_manager.setup_batch(batch)

        self.inspection_manager.load_controls.assert_called_once_with(batch)


    def should_load_control_structure(self):
        pass
    
    def should_create_one_inspector_by_branch(self):
        self.inspection_manager.controls = create_fake_control_struct()
        self.inspection_manager.create_inspectors()

        con
        assert len(self.inspection_manager.inspectors) == 3

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
