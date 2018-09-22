from unittest.mock import Mock, patch
import quactrl.models.operations as o


class An_Operation:
class A_Check:
    def should_execute(self):
        operation = Mock()
        control = Mock()
        control.method_pars = {'par': 1}
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

    @patch('quactrl.models.operations.datetime')
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

    def should_start(self):
        pass

    def should_execute(self):
        pass

    def should_be_closed(self):
        pass


    def should_be_cancelled(self):
        pass
