from unittest.mock import Mock, patch
from quactrl.services.inspection import Inspector, ControlRunner, PartInspector

import pytest


current = pytest.mark.current


class BaseTest:
    def create_patches(self, definitions):
        self.patch = {}
        self._patchers = []
        for definition in definitions:
            patcher = patch(definition)
            name = definition.split('.')[-1]
            self.patch[name] = patcher.start()
            self._patchers.append(patcher)

    def teardown_method(self, method):
        for patcher in self._patchers:
            patcher.stop()


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

    # def should_persist_results(self):
    #     pass

@pytest.mark.ahora
class An_Inspector(BaseTest):

    def setup_method(self, method):
        patches = [
            'quactrl.services.inspection.time',
            'quactrl.services.inspection.Queue',
            'quactrl.services.inspection.Test',
            'quactrl.services.inspection.Check',
            'quactrl.services.inspection.ControlRunner'
            ]
        self.create_patches(patches)

        self.service = Mock()
        self.inspector = Inspector(self.service)

    def should_create_control_runners(self):
        controls = [Mock() for _ in range(3)]
        assert len(self.inspector.control_runners) == 0

        self.inspector.load_controls(controls)

        assert self.patch['ControlRunner'].call_count == 3
        assert len(self.inspector.control_runners) == 3

    def should_eval_value(self):
        characteristic = Mock()
        characteristic.limits = [-1, 1]
        modes = ['very low', 'very high', 'a bit suspicious']
        uncertainty = 0.2

        value = 0
        failure_mode = self.inspector.eval_value(value, characteristic,
                                                 uncertainty, modes)
        assert failure_mode is None

        value = 0.81
        failure_mode = self.inspector.eval_value(value, characteristic,
                                                 uncertainty, modes)
        self.service.env.repo_fry.get.return_value.get.assert_called_with(
            'a bit suspicious very high', characteristic)

        value = 1.1
        failure_mode = self.inspector.eval_value(value, characteristic,
                                                 uncertainty, modes)
        self.service.env.repo_fry.get.return_value.get.assert_called_with('very high',
                                                                  characteristic)

        value = -0.81
        failure_mode = self.inspector.eval_value(value, characteristic,
                                                 uncertainty, modes)
        self.service.env.repo_fry.get.return_value.get.assert_called_with(
            'a bit suspicious very low', characteristic)

        value = -1.1
        failure_mode = self.inspector.eval_value(value, characteristic,
                                                 uncertainty, modes)
        self.service.env.repo_fry.get.return_value.get.assert_called_with('very low',
                                                                  characteristic)


@pytest.mark.ahora
class A_ControlRunner(BaseTest):

    def setup_method(self, method):
        patches = [
            'quactrl.services.inspection.Check'
            ]
        self.create_patches(patches)
        self.control = Mock()
        self.inspector = Mock()
        self.control_runner = ControlRunner(self.inspector, self.control)

    def should_init_loading_method(self):
        method_repo = self.inspector.service.env.method_repo

        assert self.control_runner.method == method_repo.get.return_value
        method_repo.get.assert_called_with(self.control.method_name)

    def should_count(self):
        self.control.sampling.check_is_needed.return_value = False
        assert self.control_runner.count() == None

        self.control.sampling.check_is_needed.return_value = True
        assert self.patch['Check'].return_value == self.control_runner.count()
        part = self.inspector.current_part
        self.patch['Check'].assert_called_once_with(self.inspector.test, self.control, part)

    def should_run_method(self):
        check = Mock()
        method = self.inspector.service.env.method_repo.get.return_value

        self.control_runner.run_method(check)
        method.assert_called_once_with(self.inspector, check)


@pytest.mark.ahora
class A_PartInspector(BaseTest):
    def setup_method(self, method):
        self.service = Mock()
        self.period = 1

        patches = [
            'quactrl.services.inspection.Test'
            ]
        self.create_patches(patches)
        self.inspector = PartInspector(self.service, self.period)

    def should_init_part_status(self):
        assert self.inspector._parts.empty()
        assert self.inspector.current_part is None

    def should_run_till_stop(self):
        control_runners = [Mock() for _ in range(3)]
        self.inspector.control_runners = control_runners

        self.inspector.start()
        self.inspector.stop()

        assert not self.inspector.isAlive()

    def should_wait_till_receive_a_part(self):
        pass
