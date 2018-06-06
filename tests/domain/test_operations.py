from threading import Thread
from unittest.mock import Mock, call, patch
import quactrl.domain.operations as o
import quactrl.domain.steps as s
import quactrl.domain.flows as f
from tests.domain import EmptyDataTest


class CheckRunner(Thread):
    def __init__(self, check):
        super().__init__()
        self.check = check

    def run(self):
        self.check.thread = self.thread = Mock()
        self.check.run()


class A_Check:
    def should_run_sync_check(self):
        test = f.Test()
        test.tester = Mock()

        check = o.Check(test)
        check.test = test
        check.run()

        assert test.tester.notify.mock_calls == [call(check)] * 2
        assert check.state == 'ok'

    def should_run_async_check(self):

        test = f.Test()
        test.tester = Mock()
        check = o.Check(test)
        check.test = test
        check.finish = Mock()

        check_runner = CheckRunner(check)
        check_runner.start()

        check.finished.set()
        while check_runner.is_alive():
            pass

        assert check.state == 'ok'
        assert check.finished_on
        assert check.started_on
        assert test.tester.notify.mock_calls == [call(check)] * 3

    def should_cancel_async_check_running(self):
        test = f.Test()
        test.tester = Mock()
        check = o.Check(test)
        check.test = test
        check.finish = Mock()

        check_runner = CheckRunner(check)
        check_runner.start()

        check.cancel()
        while check_runner.is_alive():
            pass

        assert check.state == 'cancelled'
        assert test.tester.notify.mock_calls == [call(check)] * 3
        check_runner.thread.cancel.assert_called_with()


class A_CheckWithHelpers(EmptyDataTest):
    def should_add_new_measures(self):
        pass

    def should_add_old_measures(self):
        pass

    def should_add_new_defects(self):
        pass

    def should_update_old_defects(self):
        pass

    def should_clean_old_defects(self):
        pass
