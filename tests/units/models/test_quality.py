from unittest.mock import Mock, patch
import quactrl.models.quality as q


# class A_Control(EmptyDataTest):
#     def should_create_a_check_instance(self):
#         control = p.Control()
#         test = f.Test()
#         test.part = Mock()
#         test.tester = Mock()

#         responsible = n.Person()
#         test.responsible = responsible

#         check = control.create_flow(test)

#         assert type(check) is f.Check
#         assert check.part == test.part
#         assert check.tester == test.tester
#         assert check.test == test
#         assert check.responsible == responsible


class A_Check:
    def setup_method(self, method):
        operation = Mock()
        control = Mock()
        responsible = Mock()

        check = q.Check(operation, control, responsible)

    def should_execute(self):
        operation = Mock()
        control = Mock()
        control.method_pars = {'par':1}
        method = control.get_method.return_value
        responsible = Mock()
        check = q.Check(operation, control, responsible)
        check.state = 'started'

        check.execute()
        method.assert_called_with(check, par=1)
        assert check.state == 'finished'

        # Testing async execution
        check.state = 'started'
        check.thread = Mock()

        check.execute()
        assert check.state == 'ongoing'

    def should_prepare(self):
        operation = Mock()
        control = Mock()
        responsible = Mock()
        check = q.Check(operation, control, responsible)
        part = Mock()
        tester = Mock()
        check.prepare(subject=part, tester=tester)

        assert check.subject == part
        assert check.tester == tester
        assert check.state == 'started'

    @patch('quactrl.models.quality.datetime')
    def should_close(self, mock_datetime):
        operation = Mock()
        control = Mock()
        responsible = Mock()
        check = q.Check(operation, control, responsible)

        # Other test
        check.state = 'finished'
        check.close()
        assert check.state == 'ok'
        assert check.finished_on == mock_datetime.datetime.now()

        check.state = 'finished'
        check.defects.append(Mock())
        check.close()
        assert check.state == 'nok'

    @patch('quactrl.models.quality.datetime')
    def should_cancel(self, mock_datetime):
        operation = Mock()
        control = Mock()
        responsible = Mock()
        check = q.Check(operation, control, responsible)
        check.state = 'ongoing'
        check.thread = Mock()

        check.cancel()
        assert check.state == 'cancelled'
        assert check.finished_on == mock_datetime.datetime.now()
        check.thread.cancel.assert_called_with()

    @patch('quactrl.models.quality.Defect')
    def should_add_defects(self, mock_Defect):
        defect = mock_Defect.return_value
        operation = Mock()
        control = Mock()
        responsible = Mock()
        failure_mode = Mock()
        check = q.Check(operation, control, responsible)
        check.subject = Mock()

        check.add_defect(failure_mode, 'tracking', 3)

        assert defect in check.defects
        mock_Defect.assert_called_with(check.subject, failure_mode, 'tracking', 3)

    @patch('quactrl.models.quality.Measurement')
    def should_add_measurements(self, mock_Measurement):
        measurement = mock_Measurement.return_value
        operation = Mock()
        control = Mock()
        responsible = Mock()
        characteristic = Mock()
        check = q.Check(operation, control, responsible)
        check.subject = Mock()
        check.add_defect = Mock()

        check.add_measurement(characteristic, 3, 'tracking')

        assert measurement in check.measurements
        mock_Measurement.assert_called_with(check.subject, characteristic, 3, 'tracking')
        failure_mode = measurement.eval.return_value
        check.add_defect.assert_called_with(failure_mode,
                                            'tracking', 1
        )

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
        characteristic.limits = [3, 6]
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
        failure = measurement.eval_value(7)
        characteristic.get_failure.assert_called_with('hi')
        assert failure == characteristic.get_failure.return_value

        # Suspicious low failure case
        failure = measurement.eval_value(7, 2)
        characteristic.get_failure.assert_called_with('shi')
        assert failure == characteristic.get_failure.return_value

        # Suspicious high failure case
        failure = measurement.eval_value(7, 2)
        characteristic.get_failure.assert_called_with('shi')
        assert failure == characteristic.get_failure.return_value


class A_Control:
    pass


class A_FailureMode:
    pass
