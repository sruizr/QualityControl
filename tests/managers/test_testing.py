from unittest.mock import Mock
from queue import Queue
import threading
import time
from tests import TestWithPatches
from quactrl.managers.testing import TestManager, Tester, Feedback
import pytest


class A_TestManager(TestWithPatches):

    def setup_method(self, method):
        patches = [
            'quactrl.managers.testing.dal',
            'quactrl.managers.testing.DevManager',
            'quactrl.managers.testing.Tester'
            ]
        self.create_patches(patches)
        # self.control = Mock()
        # self.inspector = Mock()
        self.manager = TestManager()
        self.dev_manager = self.DevManager()

    def should_set_database(self):
        self.manager.set_database('connection_string')
        self.dal.connect.assert_called_with('connection_string')

    def should_go_to_location(self):
        self.manager.go_to('loc')
        self.dev_manager.load_devs_from.assert_called_with('loc')

    def should_lazy_loading_testers(self):
        part_info = {'tracking': '123456789',
                     'part_name': 'part_name'}
        responsible_key = 'sruiz'
        mock_tester = self.Tester.return_value

        self.manager.start_test(part_info, responsible_key)
        assert self.manager.testers[0] == mock_tester
        self.Tester.assert_called_with(self.manager)
        mock_tester.orders.put.assert_called_with(
            (part_info, responsible_key, {})
        )

        self.manager.start_test(part_info, responsible_key, cavity=7, other=0)
        assert self.manager.testers[5] is None
        self.manager.testers[6] == mock_tester
        mock_tester.orders.put.assert_called_with(
            (part_info, responsible_key, {'other': 0})
        )

        test = mock_tester.test
        assert (self.manager.tests ==
                [test, None, None, None, None, None, test]
        )

    def should_stop_any_test(self):
        tester_1 = Mock()
        tester_3 = Mock()
        self.manager.testers = [ tester_1, None, tester_3]

        self.manager.stop()
        tester_1.stop.assert_called_with()
        tester_3.stop.assert_called_with()

        tester_1 = Mock()
        tester_3 = Mock()
        self.manager.testers = [ tester_1, None, tester_3]
        self.manager.stop(1)
        assert not tester_3.stop.called
        tester_1.stop.assert_called_with()


class A_Tester(TestWithPatches):

    def setup_method(self, method):
        patches = [
            'quactrl.managers.testing.dal',
            'quactrl.managers.testing.Event',
            'quactrl.managers.testing.FeedBack'
            ]
        self.create_patches(patches)
        self.manager = Mock()
        self.events = self.manager.events = Queue()
        self.tester = Tester(self.manager, cavity=2)

    def should_run_till_stops(self):
        self.tester.process = Mock()
        self.tester.start()
        self.tester.stop()

        while self.tester.join():
            pass

    def prepare_process_order(self):
        order = (
            {
                'tracking': '123456789',
                'part_number': '0000000'
            },
            'sruiz',
            {}
        )
        self.tester.set_responsible_by = Mock()
        self.tester.responsible = Mock()
        self.tester.set_control_plan_by = Mock()
        self.tester.control_plan = Mock()
        part = self.dal.get_or_create_part.return_value
        test = self.tester.control_plan.get_test.return_value
        test.checks = [Mock(name='Check_{}'.format(index))
                       for index in range(2)]

        session = self.dal.Session.return_value

        return order, test, part, session

    def should_process_order(self):
        order, test, part, session = self.prepare_process_order()

        self.tester.process(order)

        self.tester.set_responsible_by.assert_called_with('sruiz')
        self.tester.set_control_plan_for.assert_called_with(part)
        assert self.tester.events.qsize() == 6
        session.add.assert_called_with(test)
        session.commit.assert_called_with()
        assert test.part == part
        for flow in test.checks.append(test):
            for method_name in ('prepare', 'execute', 'terminate'):
                method = getattr(flow, method_name)
                method.assert_called_with()

    def should_waits_till_long_check_is_finished(self):
        class ProcessCaller(threading.Thread):
            def __init__(self, tester, order):
                super().__init__()
                self.tester = Tester
                self.order = order

            def run(self):
                self.tester.process(self.order)

        order, test, part, session = self.prepare_process_order()
        test.checks[0].result = 'ongoing'

        caller = ProcessCaller(self.tester, order)
        caller.start()
        time.sleep(1)
        assert caller.is_alive()

        test.checks[0].finished.set()

        caller.join(timeout=4.0)
        assert not caller.is_alive()

    def should_cancel_test(self):
        order, test, part, session = self.prepare_process_order()
        self.tester.cancel_test()
        self.tester.process(order)

        for check in test.checks:
            assert check.result == 'cancelled'

    def should_cancel_ongoing_check(self):
        class ProcessCaller(threading.Thread):
            def __init__(self, tester, order):
                self.tester = tester
                self.order = order

            def run(self):
                self.tester.process(self.order)

        order, test, part, session = self.prepare_process_order()
        test.checks[0].result = 'ongoing'
        caller = ProcessCaller(self.tester, order)
        caller.start()  # Waiting till check[0] finish

        assert caller.is_alive()

        self.tester.cancel_test()

        self.caller.join(timeout=0.5)
        assert not caller.is_alive()

    def should_set_responsible(self):
        responsible = Mock()
        responsible.key = 'sruiz'
        self.dal.get_responsible_by.return_value = responsible
        self.tester.set_responsible_by('sruiz')

        self.dal.get_responsible_by.assert_called_with(key='sruiz')

        self.tester.set_responsible_by('jruiz')
        self.dal.get_responsible_by.assert_called_with(key='jruiz')

    def should_set_control_plan(self):
        self.tester.location = 'location'
        self.tester.part = Mock()
        control_plan = self.dal.get_control_plan_by.return_value

        self.tester.set_control_plan_for(part)
        self.dal.get_control_plan_by.assert_called_with(
            'location', self.tester.part.resource
        )

        control_plan.has_output.return_value = False
        self.tester.part.resource = 'resource'
        self.tester.set_control_plan_for(part)
        self.dal.get_control_plan_by.assert_called_with(
            'location', 'resource'
        )

    def should_manage_feedback(self):
        data = self.tester.request_feedback({'name': None})

        assert self.events.qsize() == 2
        self.FeedBack.assert_called_with({'name': None})

        feedback = self.FeedBack.return_value
        feedback.wait.assert_called_with()
        assert data == feedback.data


class FeedbackCaller(threading.Thread):
    def __init__(self, template):
        super().__init__()
        self.feedback = Feedback(template)

    def run(self):
        self.feedback.wait()


class A_Feedback:

    def should_waits_till_receive_feedback_from_client(self):
        caller = FeedbackCaller(['data'])
        caller.start()

        assert caller.is_alive()
        caller.feedback.answer({'data': 1})

        caller.join(timeout=0.5)
        assert not caller.is_alive()

    def should_raise_exception_if_data_not_supplied(self):
        caller = FeedbackCaller(['data'])
        caller.start()
        try:
            caller.answer({})
            pytest.fails('Not exception is raised')
            caller.join(timeout=0.5)
        except Exception as e:
            pass
