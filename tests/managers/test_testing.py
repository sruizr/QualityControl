from unittest.mock import Mock
from queue import Queue
from tests import TestWithPatches
from quactrl.managers.testing import TestManager, Tester


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
        part_info = {'tracking':'123456789',
                'part_name': 'part_name'}
        responsible_key = 'sruiz'
        mock_tester = self.Tester.return_value

        self.manager.start_test(part_info, responsible_key)
        assert self.manager.testers[0] == mock_tester
        self.Tester.assert_called_with(None, self.dev_manager, self.manager.events)
        mock_tester.start.assert_called_with()
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
            'quactrl.managers.testing.dal'
            ]
        self.create_patches(patches)
        self.dev_manager= Mock()
        self.events = Queue()
        self.tester = Tester('loc',
                             self.dev_manager,
                             self.events)

    def should_run_till_stops(self):
        self.tester.process = Mock()
        self.tester.start()
        self.tester.stop()

        while self.tester.join():
            pass

    def should_process_order(self):
        order = (
            {'tracking': '123456789',
             'part_number': '0000000'
            },
            'sruiz',
            {}
        )
        self.tester.set_responsible_by = Mock()
        self.tester.responsible = Mock()
        self.tester.set_control_plan_by = Mock()
        self.tester.control_plan = Mock()

        self.tester.process(order)




    def should_set_responsible(self):
        self

    def should_set_control_plan(self):
        self
