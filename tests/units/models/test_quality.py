from unittest.mock import Mock, patch
import quactrl.models.quality as q


class A_Check:

    def should_start(self):
        operation = Mock()
        control = Mock()
        check = q.Check(operation, control)
        part = Mock()
        tester = Mock()
        check.start(subject=part, tester=tester)

        assert check.inbox['subject'] == part
        assert check.inbox['tester'] == tester
        assert check.state == 'started'

    def should_close(self):
        operation = Mock()
        control = Mock()
        check = q.Check(operation, control)

        # Other test
        check.state = 'finished'
        check.close()
        assert check.state == 'ok'
        assert check.finished_on

        check.state = 'finished'
        check.defects.append(Mock())
        check.close()
        assert check.state == 'nok'


    @patch('quactrl.models.quality.Defect')
    def should_add_defects(self, mock_Defect):
        defect = mock_Defect.return_value
        operation = Mock()
        control = Mock()
        failure_mode = Mock()
        check = q.Check(operation, control)
        check.subject = Mock()

        check.add_defect(failure_mode, 'tracking', 3)

        assert defect in check.defects
        mock_Defect.assert_called_with(check.subject, failure_mode, 'tracking',
                                       3)

    @patch('quactrl.models.quality.Measurement')
    def should_add_measurements(self, mock_Measurement):
        measurement = mock_Measurement.return_value
        operation = Mock()
        control = Mock()
        characteristic = Mock()
        check = q.Check(operation, control)
        check.subject = Mock()
        check.add_defect = Mock()

        check.add_measurement(characteristic, 3, 'tracking')

        assert measurement in check.measurements
        mock_Measurement.assert_called_with(check.subject, characteristic, 3,
                                            'tracking')
        failure_mode = measurement.eval.return_value
        check.add_defect.assert_called_with(failure_mode,
                                            'tracking', 1)


class A_Defect:
    def should_be_inserted_into_subject(self):
        subject = Mock()
        subject.defects = []
        failure_mode = Mock()
        tracking = '1234'
        qty = 5

        defect = q.Defect(subject, failure_mode, tracking, qty)
        assert defect in subject.defects


class A_Measurement:
    def should_be_inserted_into_subject(self):
        subject = Mock()
        subject.measurements = []
        characteristic = Mock()
        tracking = '1234'

        measurement = q.Measurement(subject, characteristic, tracking)
        assert measurement in subject.measurements

    def should_eval_value(self):
        characteristic = Mock()
        characteristic.limits = [3, 8]
        subject = Mock()
        tracking = '1234'
        measurement = q.Measurement(subject, characteristic, tracking)

        # Ok case
        failure = measurement.eval_value(4)
        assert failure is None

        # Low failure case
        failure = measurement.eval_value(2)
        characteristic.get_failure.assert_called_with('lo')
        assert failure == characteristic.get_failure.return_value

        # High failure case
        failure = measurement.eval_value(9)
        characteristic.get_failure.assert_called_with('hi')
        assert failure == characteristic.get_failure.return_value

        # Suspicious low failure case
        failure = measurement.eval_value(4, 2)
        characteristic.get_failure.assert_called_with('slo')
        assert failure == characteristic.get_failure.return_value

        # Suspicious high failure case
        failure = measurement.eval_value(7, 1)
        characteristic.get_failure.assert_called_with('shi')
        assert failure == characteristic.get_failure.return_value

        # No limits
        characteristic.limits = [None, None]
        assert measurement.eval_value(1000) is None


class A_Control:
    def should_insert_into_route(self):
        route = Mock()
        route.steps = []
        part_group = Mock()
        characteristic = Mock()

        control = q.Control(route, part_group, characteristic)
        assert control in route.steps
        assert control.sequence == 0
        assert control.last_count == 0

        other_control = q.Control(route, part_group, characteristic)
        assert other_control.sequence == 1

    @patch('quactrl.models.quality.get_function')
    def should_get_method(self, mock_get):
        route = Mock()
        route.steps = []
        part_group = Mock()
        characteristic = Mock()
        method = 'method_name'
        control = q.Control(route, part_group, characteristic, method=method)

        method = control.get_method()
        mock_get.assert_called_with('method_name')
        assert method == mock_get.return_value

    @patch('quactrl.models.quality.get_function')
    def should_get_reaction(self, mock_get):
        route = Mock()
        route.steps = []
        part_group = Mock()
        characteristic = Mock()
        reaction = 'reaction_name'
        control = q.Control(route, part_group, characteristic,
                            reaction=reaction)
        method = control.get_reaction()

        mock_get.assert_called_with('reaction_name')
        assert method == mock_get.return_value

    @patch('quactrl.models.quality.Check')
    @patch('quactrl.models.quality.Sampling')
    def should_create_action_if_necessary(self, mock_Sampling, mock_Check):
        sampling = mock_Sampling.return_value
        route = Mock()
        route.steps = []
        part_group = Mock()
        characteristic = Mock()
        sampling = '100%'
        method = 'method_name'
        reaction = 'reaction_name'
        control = q.Control(route, part_group, characteristic, sampling,
                            method, reaction)
        assert mock_Sampling.return_value == control.sampling

        operation = Mock()
        mock_Sampling.return_value.count.return_value = True
        check = control.create_action(operation)
        assert check == mock_Check.return_value

        mock_Sampling.return_value.count.return_value = False
        assert control.create_action(operation) is None


class A_FailureMode:
    def should_insert_into_characteristic(self):
        characteristic = Mock()
        characteristic.failure_modes = {}
        failure = q.FailureMode(characteristic, 'low')

        assert failure == characteristic.failure_modes['low']


class Sampling:
    def should_count_operation(self):
        control = Mock()
        control.last_count = 0
        operation = Mock()
        operation.part.qty = 2
        sampling = q.Sampling(control, 1, 1)

        assert sampling.count(operation)
        assert control.last_count == 2
