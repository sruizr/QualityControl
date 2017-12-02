import time
from unittest.mock import Mock, patch
from quactrl.services.inspection import Inspector, ControlRunner, InspectionSession
import pytest


current = pytest.mark.current


class TestWithPatches:
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
class An_InspectionSession:

    def setup_method(self, method):
        self.inspector = Mock()
        self.inspector.control_runners = [Mock() for _ in range(30)]


    def should_work_on_continuous(self):
        inspection_session = InspectionSession(self.inspector, resolution=0)
        inspection_session.start()
        assert inspection_session.is_alive()

        inspection_session.stop_session()
        assert not inspection_session.is_alive()

    def should_work_on_cycles(self):
        inspection_session = InspectionSession(self.inspector)

        inspection_session.start()
        assert  not inspection_session.init_cycle_event.is_set()
        inspection_session.init_cycle()
        time.sleep(0.25)
        assert self.inspector.service.check_initialized.called
        assert self.inspector.service.check_finished.called

        inspection_session.stop_session()
        assert not inspection_session.is_alive()

    def should_stop_cycle_when_async_method(self):

        # control_runners[5] has an async method
        check = Mock(name='check')
        check.state = 'ongoing'
        self.inspector.control_runners[5].count.return_value = check
        self.inspector.control_runners[5].run = lambda s: time.sleep(0.5)

        inspection_session = InspectionSession(self.inspector)
        inspection_session.start()
        inspection_session.init_cycle()
        time.sleep(0.25)
        assert not self.inspector.control_runners[6].run.called

        inspection_session.stop_cycle()
        time.sleep(1)
        assert check.cancel.called
        assert self.inspector.test.state == 'cancelled'
        assert check.state == 'cancelled'

        assert not self.inspector.control_runners[6].run.called

        inspection_session.stop_session()
        assert not inspection_session.is_alive()

    def should_stop_cycle_on_mid_sequence(self):
        self.inspector.control_runners[5].run = lambda: time.sleep(0.5)

        inspection_session = InspectionSession(self.inspector)
        inspection_session.start()
        inspection_session.init_cycle()
        time.sleep(0.25)
        assert not self.inspector.control_runners[6].run.called

        inspection_session.stop_cycle()
        assert not self.inspector.control_runners[6].run.called

        inspection_session.stop_session()
        assert not inspection_session.is_alive()

@pytest.mark.ahora
class An_Inspector(TestWithPatches):

    def setup_method(self, method):
        patches = [
            'quactrl.services.inspection.time',
            'quactrl.services.inspection.Test',
            'quactrl.services.inspection.Check',
            'quactrl.services.inspection.InspectionSession'
            ]
        self.create_patches(patches)
        self.service = Mock()

    def should_init_properly(self):
        inspector = Inspector(self.service)

    def should_setup_batch(self):
        controls = [Mock() for _ in range(3)]
        assert len(self.inspector.control_runners) == 0

        self.inspector.setup_batch(controls)

        assert self.patch['ControlRunner'].call_count == 3
        assert len(self.inspector.control_runners) == 3

    def should_eval_value(self):
        characteristic = Mock()
        characteristic.limits = [-1, 1]
        modes = ['very low', 'very high', 'a bit suspicious']
        uncertainty = 0.2
        # TODO: Check if one of the limits is ommited
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
class A_ControlRunner(TestWithPatches):

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
