from unittest.mock import Mock
from queue import Queue
import threading
from tests import TestWithPatches
from quactrl.managers.testing import TestManager, Tester, Feedback
import pytest


class A_TestManager(TestWithPatches):
    def setup_method(self, method):
        patches = [
            'quactrl.managers.testing.dal',
            'quactrl.managers.testing.DeviceManager',
            'quactrl.managers.testing.Tester'
            ]
        self.create_patches(patches)
        # self.control = Mock()
        # self.inspector = Mock()
        self.manager = TestManager()
        self.dev_manager = self.DeviceManager()

        self.manager.testers = [Mock() for _ in range(3)]
        self.manager.events = [[] for _ in range(3)]

    def should_connect(self):
        pars = {'connection_string': 'conn'}
        self.manager.connect(**pars)
        self.dal.connect.assert_called_with(**pars)

    def should_setup(self):
        pars = {'location_key': 'loc',
                'process_key': 'p_key',
                'cavities': 3,
                'till_first_failure': False,
                'create_part': False
        }
        self.manager.setup(**pars)

        assert self.manager.cavities == 3
        assert len(self.manager.testers) == 3
        assert not self.manager.tff
        assert self.manager.location_key == 'loc'
        assert self.manager.process_key == 'p_key'

        self.dev_manager.load_devs_from.assert_called_with('loc')

    def should_start_tests(self):
        part_info = {'tracking': '123456789',
                     'part_name': 'part_name'}
        responsible_key = 'sruiz'

        self.manager.start_test(part_info, responsible_key, 2)

        self.manager.testers[2].orders.put((part_info, responsible_key))

    def should_notify_to_tester(self):
        self.manager.notify('info', 2)

        self.manager.testers[2].notify.assert_called_with('info')

    def should_download_events_from_cavity(self):

        cavity_events = self.manager.testers[2].empty_events.return_value = [Mock()]

        events = self.manager.download_events(2)

        assert events == cavity_events
        assert self.manager.events[2] == cavity_events

    def should_download_all_events(self):
        expected_events = []
        for tester in self.manager.testers:
            events = tester.empty_events.return_value = [Mock()]
            expected_events.append(events)

        events = self.manager.download_events(None)

        assert expected_events == events
        assert expected_events == self.manager.events

    def should_stop_all_tests(self):
        self.manager.testers = [Mock() for _ in range(3)]
        testers = [tester for tester in self.manager.testers]
        for index, tester in enumerate(testers):
            tester.stop.return_value = [index]

        result  = self.manager.stop()
        for tester in testers:
            tester.stop.assert_called_with()
        assert result == [0, 1, 2]
        assert self.Tester.call_count == 3

    def should_stop_only_one_tester(self):
        testers = [Mock() for _ in range(3)]
        self.manager.testers = [tester for tester in testers]
        for index, tester in enumerate(testers):
            tester.stop.return_value = [index]

        result = self.manager.stop(1)

        testers[1].stop.assert_called_with()
        assert result == [1]

        assert self.Tester.call_count == 1


class A_Tester(TestWithPatches):
    def setup_method(self, method):
        patches = [
            'quactrl.managers.testing.dal',
            'quactrl.managers.testing.qry',
            'quactrl.managers.testing.Event',
            'quactrl.managers.testing.Feedback'
            ]
        self.create_patches(patches)
        self.manager = Mock()
        self.events = Queue()
        self.tester = Tester(self.manager)

    def teardown_method(self, method):
        if self.tester.is_alive():
            self.tester.stop()

    def should_get_process_pars_from_manager(self):
        assert self.tester.ttf == self.manager.ttf
        assert self.tester.create_part == self.manager.create_part

        assert self.tester.process == self.qry.get_process.return_value
        self.qry.get_process.assert_called_with(self.manager.process_key)
        assert self.tester.location == self.qry.get_location.return_value
        self.qry.get_location.assert_called_with(self.manager.location_key)
        assert self.tester.dev_manager == self.manager.dev_manager

    def should_run_till_stops(self):
        self.tester.process = Mock()
        self.tester.start()
        self.tester.stop()

        self.tester.join(timeout=1)
        assert not self.tester.is_alive()

    def prepare_process_order(self):
        order = (
            {
                'tracking': '123456789',
                'part_number': '00000000'
            },
            'sruiz'
        )

        self.tester.set_responsible_by = Mock()
        self.tester.responsible = Mock()
        self.tester.set_control_plan_for = Mock()
        self.tester.control_plan = Mock()
        self.control_plan.steps = [Mock() for _ in range(2)]
        self.tester.get_or_create_part = Mock()

        part = self.dal.get_or_create_part.return_value
        test = self.tester.control_plan.get_test.return_value

        test.checks = [Mock(name='Check_{}'.format(index))
                       for index in range(2)]

        session = self.dal.Session.return_value

        return order, test, part, session

    @pytest.mark.current
    def should_process_order(self):
        order, test, part, session = self.prepare_process_order()

        self.tester.process_test(order)

        self.tester.set_responsible_by.assert_called_with('sruiz')
        self.tester.set_control_plan_for.assert_called_with(part)

        assert self.tester.events.qsize() == 6
        session.add.assert_called_with(test)
        session.commit.assert_called_with()
        assert test.part == part
        for flow in test.checks:
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
                super().__init__()
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

        caller.join(timeout=0.5)
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
        control_plan = self.dal.get_control_plan_by.return_value
        part = Mock()
        part.resource = 'resource'

        self.tester.set_control_plan_for(part)
        self.dal.get_control_plan_by.assert_called_with(
            'location', part.resource
        )

        control_plan.has_output.return_value = False
        self.tester.set_control_plan_for(part)

        self.dal.get_control_plan_by.assert_called_with(
            'location', 'resource'
        )

    def should_manage_feedback(self):
        data = self.tester.request_feedback({'name': None})

        assert self.events.qsize() == 2
        self.Feedback.assert_called_with({'name': None})

        feedback = self.Feedback.return_value
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
            assert not caller.is_alive()
        except Exception as e:
            caller.feedback.set()
