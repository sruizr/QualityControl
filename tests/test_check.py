from tests import TestBase
from datetime import datetime
from unittest.mock import Mock, patch
from quactrl.resources import (
    Element, Operation
)
from quactrl.plan import (
    Characteristic, Sampling, Reaction, Method, FailureMode, Control
)

from quactrl.check import (
    Sample, Test, Check, Result
    )

from pytest import mark
import pdb


class A_Test(TestBase):

    def setup_method(self, method):
        test_plan = Mock()
        test_plan.controls = [Mock() for _ in range(3)]
        for control in test_plan.controls:
            control.characteristic = Mock()

        sample = Mock()
        operator = Mock()

        self.test = Test(test_plan, sample, operator)
    """Defines procedure for creating and filling a test report(database)"""

    @mark.current
    @patch('quactrl.check.datetime')
    @patch('quactrl.check.dal')
    def should_init(self, mock_dal, mock_datetime):
        now = datetime(2000, 1, 1)
        mock_datetime.now.return_value = now

        test_plan = self.helper.get_test_plan()
        mock_dal.query.return_value = test_plan

        process = Mock()
        sample = Mock()
        user = Mock()
        measure_system = Mock()

        test = Test(process,
                    sample,
                    user,
                    measure_system)

        assert test.user == user
        assert len(test.checks) == len(test_plan.controls)

        for check, control in zip(test.checks, test.controls):
            assert check.characteristic == control.characteristic

        assert test.sample == sample
        assert test.measure_sytem == measure_system
        assert test.open_date == now

        mock_dal.session.commit.assertis_called()

    @patch('quactrl.check.dal')
    def should_eval_test_from_check_evals(self, mock_dal):
        test = self.load_simple_test()
        test.checks = [Mock(), Mock()]

        assert test.eval() == 'Pending'

        check = test.checks[0]
        check.eval.return_value = 'OK'
        mock_dal.commit.assert_called_with()
        assert test.eval() == Result.PENDING

        test.checks[1].eval.return_value = 'NOK'
        assert test.eval() == Result.NOK

        test.check[1].eval.return_value = 'OK'
        assert test.eval() == Result.OK

    @patch('quactrl.check.datetime')
    @patch('quactrl.check.dal')
    def should_close_with_result_ok(self, mock_dal, mock_datetime):
        now = datetime(2017, 1, 2)
        mock_datetime.now.return_value = now
        test = self.load_simple_test()

        test.eval = Mock()
        test.eval.return_value = 'OK'
        test.close()

        assert test.close_date == now
        assert test.result == 'OK'
        mock_dal.session.commit.assert_called_with(test)

    @patch('quactrl.check.datetime')
    @patch('quactrl.check.dal')
    def should_close_with_result_Nok(self, mock_dal, mock_datetime):
        now = datetime(2017, 1, 2)
        mock_datetime.now.return_value = now

        test = self.load_simple_test()

        test.eval = Mock()
        test.eval.return_value = 'NOK'
        test.close()

        assert test.close_date == now
        assert test.result == 'OK'
        mock_dal.session.commit.assert_called_with(test)

    def should_persist_results(self):
        pass


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

