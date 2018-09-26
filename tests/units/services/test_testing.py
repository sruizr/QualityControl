from unittest.mock import Mock, call
from queue import Queue
import threading
# from tests import TestWithPatches
# from quactrl.managers.testing import TestManager, Tester, Feedback
# from quactrl.domain.flows import Test, Check
import pytest


class A_TestingService:

    def should_load_with_persistence_layer(self):
        pass
 #     def should_connect(self):
#         pars = {'conn_string': 'conn'}
#         self.manager.connect(**pars)
#         self.dal.connect.assert_called_with(**pars)

#     def should_setup(self):
#         pars = {'location_key': 'loc',
#                 'process_key': 'p_key',
#                 'cavities': 3,
#                 'till_first_failure': False,
#                 'create_part': False
#         }
#         self.manager.setup(**pars)

#         assert self.manager.cavities == 3
#         assert len(self.manager.testers) == 3
#         assert not self.manager.tff
#         assert self.manager.location_key == 'loc'
#         assert self.manager.process_key == 'p_key'

#         self.dev_manager.load_devs_from.assert_called_with('loc')

#     def should_start_tests(self):
#         part_info = {'tracking': '123456789',
#                      'part_name': 'part_name'}
#         responsible_key = 'sruiz'

#         self.manager.start_test(part_info, responsible_key, 2)

#         self.manager.testers[2].orders.put((part_info, responsible_key))

#     def should_notify_to_tester(self):
#         self.manager.notify('info', 2)

#         self.manager.testers[1].notify.assert_called_with('info')

#     def should_download_events_from_cavity(self):
#         cavity_events = self.manager.testers[1].empty_events.return_value = [Mock()]

#         events = self.manager.download_events(2)

#         assert events == cavity_events
#         assert self.manager.events[1] == cavity_events

#     def should_download_all_events(self):
#         expected_events = []
#         for tester in self.manager.testers:
#             events = tester.empty_events.return_value = [Mock()]
#             expected_events.append(events)

#         events = self.manager.download_events(None)

#         assert expected_events == events
#         assert expected_events == self.manager.events

#     def should_stop_all_tests(self):
#         self.manager.testers = [Mock() for _ in range(3)]
#         testers = [tester for tester in self.manager.testers]
#         for index, tester in enumerate(testers):
#             tester.stop.return_value = [index]

#         result  = self.manager.stop()
#         for tester in testers:
#             tester.stop.assert_called_with()
#         assert result == [0, 1, 2]
#         assert self.Tester.call_count == 3

#     def should_stop_only_one_tester(self):
#         testers = [Mock() for _ in range(3)]
#         self.manager.testers = [tester for tester in testers]
#         for index, tester in enumerate(testers):
#             tester.stop.return_value = [index]

#         result = self.manager.stop(1)

#         testers[0].stop.assert_called_with()
#         assert result == [0]

#         assert self.Tester.call_count == 1


# @pytest.mark.current
# class A_Tester(TestWithPatches):
#     def setup_method(self, method):
#         patches = [
#             'quactrl.managers.testing.dal',
#             'quactrl.managers.testing.qry',
#             'quactrl.managers.testing.Event',
#             'quactrl.managers.testing.Feedback'
#             ]
#         self.create_patches(patches)
#         self.manager = Mock()
#         self.tester = Tester(self.manager)

#     def teardown_method(self, method):
#         super().teardown_method(method)
#         if self.tester.is_alive():
#             self.tester.stop()

#     def should_get_process_pars_from_manager(self):
#         assert self.tester.tff == self.manager.tff
#         assert self.tester.create_part == self.manager.create_part

#         assert self.tester.process == self.qry.get_process_by.return_value
#         self.qry.get_process_by.assert_called_with(self.manager.process_key)
#         assert self.tester.location == self.qry.get_location.return_value
#         self.qry.get_location.assert_called_with(self.manager.location_key)
#         assert self.tester.dev_manager == self.manager.dev_manager

#     def should_run_till_stops(self):
#         self.tester.process = Mock()
#         self.tester.start()
#         self.tester.stop()

#         self.tester.join(timeout=1)
#         assert not self.tester.is_alive()

#     def prepare_process_order(self):
#         order = (
#             {
#                 'tracking': '123456789',
#                 'part_number': '00000000'
#             },
#             'sruiz'
#         )

#         self.tester.set_responsible_by = Mock()
#         self.tester.responsible = Mock()
#         self.tester.set_control_plan_for = Mock()
#         control_plan = Mock(name='control_plan')
#         controls = [Mock() for _ in range(2)]
#         for control in controls:
#             control.pars = {}
#         control_plan.steps = controls
#         control_plan.create_flow.return_value = Mock(spec=Test)
#         self.tester.control_plan = control_plan

#         self.tester.get_or_create_part = Mock()

#         self.tester.get_or_create_part = Mock()
#         part = self.tester.get_or_create_part.return_value

#         test.checks = [Mock(name='Check_{}'.format(index))
#                        for index in range(2)]

#         session = self.dal.Session.return_value

#         return order, test, part, session

#     def should_get_or_create_part(self):
#         pass

#     def should_process_order(self):
#         order, test, part, session = self.prepare_process_order()
#         self.tester.request_feedback = Mock()

#         self.tester.process_test(order)

#         self.tester.set_responsible_by.assert_called_with('sruiz')
#         self.tester.set_control_plan_for.assert_called_with(part)

#         assert call(test) in session.add.mock_calls
#         session.commit.assert_called_with()

#     def should_manage_feedback_when_process_order(self):
#         order, test, part, session = self.prepare_process_order()
#         self.tester.request_feedback = Mock()

#         pars = {'message': 1, 'answer_fields': 2}
#         for control in self.tester.control_plan.steps:
#             control.pars = {'pre_feedback': pars,
#                             'post_feedback': pars}

#         self.tester.process_test(order)
#         assert self.tester.request_feedback.mock_calls == [
#             call(message=1, answer_fields=2)] * 4

#     def should_cancel_test(self):
#         order, test, part, session = self.prepare_process_order()
#         self.tester.cancel_test()
#         self.tester.process_test(order)

#         test.cancel.assert_called_with()
#         # for check in test.checks:
#         #     assert check.state == 'cancelled'

#     def should_cancel_ongoing_check(self):
#         self.tester._current_check = Mock()
#         self.tester._current_check.state = 'ongoing'

#         self.tester.cancel_test()

#         assert self.tester.cancel_signal
#         self.tester._current_check.cancel.assert_called_with()

#     def should_set_responsible(self):
#         responsible = Mock()
#         responsible.key = 'sruiz'
#         self.qry.get_responsible_by.return_value = responsible
#         self.tester.set_responsible_by('sruiz')

#         self.qry.get_responsible_by.assert_called_with(key='sruiz')

#         self.tester.set_responsible_by('jruiz')
#         self.qry.get_responsible_by.assert_called_with(key='jruiz')

#     def should_set_control_plan(self):
#         self.tester.location = Mock()
#         self.tester.process = Mock()
#         control_plan = self.qry.get_control_plan_by.return_value
#         part = Mock()

#         self.tester.set_control_plan_for(part)
#         self.qry.get_control_plan_by.assert_called_with(
#             location=self.tester.location,
#             process=self.tester.process,
#             part_model=part.part_model
#         )

#         control_plan.has_output.return_value = False
#         self.tester.set_control_plan_for(part)

#         self.qry.get_control_plan_by.assert_called_with(
#             location=self.tester.location,
#             process=self.tester.process,
#             part_model=part.part_model
#         )

#     def should_manage_feedback(self):
#         self.Feedback.return_value.data = Mock()
#         data = self.tester.request_feedback('message', 'fields')

#         assert self.tester.events.qsize() == 2
#         feedback = self.Feedback.return_value
#         self.Feedback.assert_called_with('message', 'fields')
#         feedback.wait.assert_called_with()

#         assert data == feedback.data
