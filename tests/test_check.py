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
    Sample, Test, Check
)

from pytest import mark
import pdb


class A_Test(TestBase):

    """Defines procedure for creating and filling a test report(database)"""
    @patch('quactrl.do.time')
    @patch('quactrl.do.dal')
    def should_init(self, mock_dal, mock_time):
        now = datetime.datetime(2000, 1, 1)
        mock_time.now.return_value = now

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

    def should_eval_test_from_check_evals(self, mock_dal):
        test = self.load_simple_test()
        test.checks = [Mock(), Mock()]

        assert test.eval() == 'Pending'

        check = test.checks[0]
        check.eval.return_value = 'OK'
        mock_dal.commit.assert_called_with()
        assert test.eval() == 'Pending'

        test.checks[1].eval.return_value = 'NOK'
        assert test.eval() == 'NoOK'

        test.check[1].eval.return_value = 'OK'
        assert test.eval() == 'OK'



    def should_close_with_result_ok(self, mock_dal, mock_time):
        now = datetime.datetime(2017, 1, 2)
        mock_time.now.return_value = now

        test = self.load_simple_test()

        test.eval = Mock()
        test.eval.return_value = 'OK'
        test.close()

        assert test.close_date == now
        assert test.result == 'OK'
        mock_dal.session.commit.assert_called_with(test)

    def should_close_with_result_Nok(self, mock_dal, mock_time):
        now = datetime.datetime(2017, 1, 2)
        mock_time.now.return_value = now

        test = self.load_simple_test()

        test.eval = Mock()
        test.eval.return_value = 'NOK'
        test.close()

        assert test.close_date == now
        assert test.result == 'OK'
        mock_dal.session.commit.assert_called_with(test)

    def should_(self):
        pass

class A_Check:

    def setup_method(self, method):
        control = Mock()
        control.characteristic = Mock()
        test = Mock()
        self.check = Check(control, test)

    @patch('quactrl.do.dal')
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
        assert check.measurements[check.characteristic] is None

        # Value characteristic with array value
        control.characteristic.specs = [[1,2], [1, 2]]
        check = Check(test, control)
        assert len(check.measurements[check.characteristic]) == 2

        # Basic attribute characteristic
        control.characteristic.specs = 'abc'
        check = Check(test, control)
        assert control.characteristic not in check.measurements.keys()

        # Characteristic with children
        control.characteristic.children = [Mock() for _ in range(3)]
        check = Check(test, control)
        for characteristic in control.characteristic.children:
            assert check.measurements[characteristic] is None

    @mark.current
    def should_eval_measure_simple_value(self):
        check = self.check
        characteristic = Mock()
        characteristic.limits = [1, 2]
        del characteristic.modes
        check.add_measure = Mock()

        check.control.characteristic = characteristic

        value = 1.5
        check.eval_measure(value, characteristic)
        assert len(check.failures) == 0
        check.add_measure.assert_called_with(value, characteristic)

        value = 3
        check.eval_measure(value, characteristic)
        failure = check.failures[-1]
        assert failure.mode == 'high'
        assert failure.index == None
        check.add_measure.assert_called_with(value, characteristic)

        value = 0
        check.eval_measure(value, characteristic)
        assert check.failures[-1].mode == 'low'
        assert check.failures[0].index == 1
        assert check.failures[1].index == 2
        check.add_measure.assert_called_with(value, characteristic)

    @mark.current
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


    @mark.current
    def should_process_results(self):
        pass

    @patch('quactrl.do.dal')
    def should_create_measurements(self, mock_dal):
        now = datetime.datetime(2017, 5, 1)
        mock_time.time.return_value = now

        # Atribute characteristic with failure: NOK
        failure = Mock()
        test.checks[2].result_is(None, failures=failure)

        # Value characteristic
        test.checks[3].result_is(value, failures=failure)

        # Characteristic with children
        check.control.characteristic = Mock()
        check.control.characteristic.children = [Mock() for _ in range(3)]

        check.result_is(failures=[])

    @patch('quactrl.do.dal')
    def should_create(self, mock_dal):
        pass

    @patch('quactrl.do.dal')
    def should_execute(self, mock_dal):

        self.check.record_result = Mock()

        self.check.execute()

        self.check.record_result.assert_called_with()
