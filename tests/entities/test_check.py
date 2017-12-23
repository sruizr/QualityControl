from tests import TestBase
from datetime import datetime
from unittest.mock import Mock, patch, call
from quactrl.resources import (
    Element, Operation
)
from quactrl.plan import (
    Characteristic, Sampling, FailureMode, Control, ControlPlan
)

from quactrl.entities.check import (
    Test, Check, Result, Inspector
    )

from pytest import mark
import pdb


@mark.current
class A_Test(TestBase):

    def setup_method(self, method):
        """Defines procedure for creating and filling a test report(database)"""
        self.test_plan = Mock()
        self.controls = [Mock() for _ in range(3)]
        for control in self.controls:
            control.characteristic = Mock()
            control.measure_systems = ['ms1', 'ms2']

        self.sample = Mock()
        self.verifier = Mock()

        self.dal_patcher = patch('quactrl.check.dal')
        self.factories_patcher = patch('quactrl.factories')
        self.check_patcher = patch('quactrl.check.Check')

        self.mock_dal = self.dal_patcher.start()
        self.mock_factories = self.factories_patcher.start()
        self.mock_check= self.check_patcher.start()
        self.mock_check.side_effect = [Mock() for _ in range(3)]

        Test.checks = []

    def teardown_method(self, method):
        self.dal_patcher.stop()
        self.mock_factories.stop()
        self.mock_check.stop()

    def should_init(self):

        test = Test(self.controls, self.sample, self.verifier)

        assert test.verifier == self.verifier
        assert len(self.controls) == len(test.checks)
        assert test.state == Result.PENDING

        for control, arg_call in zip(self.controls, self.mock_check.Check.call_args_list):
            assert call(test, control) == arg_call

        assert test.sample == self.sample

        self.mock_dal.Session.assert_called_with()
        session = self.mock_dal.Session()
        session.add.assert_called_with(test)
        session.commit.assert_called_with()


    def should_eval_test_from_check_states(self):
        test = Test(self.controls, self.sample, self.verifier)

        for check in test.checks:
            check.state = Result.PENDING

        assert test.eval() == Result.PENDING

        test.checks[0].state = Result.OK
        assert test.eval() == Result.ONGOING

        test.checks[1].state = Result.NOK
        assert test.eval() == Result.NOK

        test.checks[1].state = Result.OK
        test.checks[2].state = Result.SUSPICIOUS
        assert test.eval() == Result.SUSPICIOUS

        test.checks[2].state = Result.OK
        assert test.eval() == Result.OK

    @patch('quactrl.check.datetime')
    def should_close(self, mock_datetime):
        now = datetime(2017, 1, 2)
        mock_datetime.now.return_value = now
        test = Test(self.controls, self.sample, self.verifier)

        test.eval = Mock()
        test.eval.return_value = Result.OK
        test.close()

        assert test.close_date == now
        assert test.state == Result.OK
        test.session.commit.assert_called_with()

        test.eval.return_value = Result.ONGOING
        test.close()
        assert test.state == Result.CANCELLED


    def should_execute_checks_sequentially(self):

        test = Test(self.controls, self.sample, self.verifier)

        test.execute()

        for check in test.checks:
            check.execute.assert_called_with()


@mark.current
class A_Check:

    def setup_method(self, method):
        control = Mock()
        control.characteristic = Mock()
        test = Mock()
        self.check = Check(test, control)

    @patch('quactrl.check.dal')
    def should_init(self, mock_dal):
        control = Mock()
        control.characteristic = Mock()
        sample = Mock()
        test = Mock()

        # Basic value characteristic
        control.characteristic.limits = [1, 2]
        check = Check(test, control)
        assert check.test == test
        assert check.control == control
        assert check.failures == []
        assert len(check.measures) == 0
        assert check.state == Result.PENDING
        assert hasattr(check, 'method')

    def should_eval_measure_simple_value(self):
        check = self.check
        characteristic = Mock()
        characteristic.limits = [1, 2]
        del characteristic.modes

        check.control.characteristic = characteristic

        value = 1.5
        check.eval_measure(value, characteristic)
        assert len(check.failures) == 0
        assert len(check.measures) == 1
        assert check.measures[characteristic] == value

        value = 3
        check.eval_measure(value, characteristic)
        failure = check.failures[-1]
        assert failure.mode == 'high'
        assert failure.index == 1
        assert len(check.measures[characteristic]) == 2

        value = 0
        check.eval_measure(value, characteristic)
        assert check.failures[-1].mode == 'low'
        assert check.failures[-1].index == 2
        assert check.measures[characteristic][-1] == value

    def should_add_measure(self):
        check = self.check
        characteristic = Mock()
        characteristic.limits = [None, None]

        value_1 = 1
        check.add_measure(value_1, characteristic)
        assert check.measures[characteristic] == value_1

        value_2 = 4
        check.add_measure(value_2, characteristic)
        assert check.measures[characteristic] == [value_1, value_2]

        value_3 = 4
        check.add_measure(value_3, characteristic)
        assert check.measures[characteristic] == [value_1, value_2, value_3]

    def should_process_results_changing_state(self):
        """From measures and evaluations fixes a check state"""
        check = self.check

        check.process_results()
        assert check.state == Result.OK

        mock_failure = Mock()
        check.failures = [mock_failure]
        check.process_results()
        assert check.state == Result.NOK

    def should_process_results_updating_relations(self):
        check = self.check
        raise NotImplementedError()


    @patch('quactrl.check.datetime')
    def should_execute(self, mock_datetime):
        begin = datetime(2017, 1, 1)
        end = datetime(2017,1,2)
        mock_datetime.now.side_effect = [begin, end]

        check = self.check
        check.method = Mock()
        check.process_results = Mock()
        observer = Mock()

        check.execute(observer)

        assert check.open_date == begin
        assert check.close_date == end
        observer.update.assert_called_with(check)


@mark.current
class An_Inspector:
    def setup_method(self, method):
        controls = [ Mock() for _ in range(2)]
        inspector_manager = Mock()
        self.inspector = Inspector(inspector_manager)
        batch = Mock()
        self.inspector.setup_batch(batch)
        self.inspector.controls = controls

    def should_wait_till_part_signal(self):
        self.inspector.start()
        assert self.inspector.test is None

        self.inspector.take_unit(part)
        assert self.inspector.test is not None
        assert len(self.inspector.test.checks) == 2

    def should_run_test_sequence(self):
        inspector_manager = Mock()
        part = Mock()
        inspector = Inspector(inspector_manager)
        inspector.start()
        inspector.take_unit(part)
        assert inspector.test
        assert len(inspector.test.checks) == 2

    def should_eval_measure(self):
        pass

    def should_setup_batch(self):
        pass

    def should_persist_results(self):
        pass
