from unittest.mock import Mock
import time
from ...units import TestWithPatches
import threading
import quactrl.services.testing as t
import pytest


class A_TestingService(TestWithPatches):
    def setup_method(self, method):
        super().create_patches([
            'quactrl.services.testing.Inspector',
            'quactrl.services.testing.DeviceContainer'
        ])
        self.db = Mock()
        self.service = t.Service(self.db, 'location')

    def should_init_without_cavities(self):
        serv = t.Service(self.db, 'location')

        assert serv.cavities == 1
        assert serv.active_cavities == [None]
        self.Inspector.assert_called_with(
            serv.db, serv.dev_container, 'location',  None, True
        )
        inspector = self.Inspector.return_value
        inspector.start.assert_called_with()

    def should_init_with_all_cavities(self):
        serv = t.Service(self.db, 'location', 5)

        assert serv.cavities == 5
        for cavity in range(5):
            assert cavity in serv.inspectors.keys()

    def should_init_with_some_cavities(self):
        serv = t.Service(self.db, 'location', [2, 3])

        assert serv.cavities == 2
        for cavity in [2, 3]:
            assert cavity in serv.inspectors.keys()

    def _should_raise_exception_when_there_are_inspectors_working(self):
        serv = self.service

        serv.inspectors = {1: Mock()}
        try:

            pytest.fail('No InspectorException raised')
        except t.InspectorException:
            pass

    def should_stack_part_on_cavity(self):
        serv = self.service
        inspector = Mock()
        serv.inspectors = {1: inspector}

        serv.stack_part('part_info', 'responsible_key', 1)

        inspector.orders.put.assert_called_with(
            ('part_info', 'responsible_key')
        )

    def should_tear_down(self):
        pass

    def should_stop_inspector(self):
        pass

    def should_restart_inspector(self):
        pass


class An_Inspector(TestWithPatches):

    def setup_method(self, method):
        self.create_patches([
            'quactrl.services.testing.Question',
            'quactrl.services.testing.op.Part'
        ])

    def should_have_correct_name(self):
        inspector = t.Inspector(Mock(), Mock(), 'loc')
        assert inspector.name == 'Inspector'

        inspector = t.Inspector(Mock(), Mock(), 'loc', cavity=7)
        assert inspector.name == 'Inspector_7'

    def should_set_responsible(self):
        db = Mock()
        inspector = t.Inspector(db, Mock(), 'loc')
        responsible = db.Persons().get.return_value

        inspector.set_responsible('responsible')

        assert responsible == inspector.responsible

        inspector.set_responsible('other')
        assert db.Persons().get.call_count == 2
        db.Persons().get.assert_called_with('other')

    def should_set_part_model(self):
        db = Mock()
        inspector = t.Inspector(db, Mock(), 'loc')

        get_part_model = db.PartModels().get
        get_control_plan = db.ControlPlans().get_by

        inspector.set_part_model('part_number')
        assert inspector.part_model == get_part_model.return_value
        assert inspector.control_plan == get_control_plan.return_value

        get_part_model.assert_called_with('part_number')
        get_control_plan.assert_called_with(
            inspector.part_model,
            db.Locations().get.return_value)

    def should_get_part_from_part_info(self):
        db = Mock()
        inspector = t.Inspector(db, Mock(), 'loc')
        inspector.part_model = Mock()
        inspector.location = Mock()

        get_part = db.Parts().get_by
        get_part.return_value = None
        expected_part = self.Part.return_value
        expected_part.location = inspector.location

        part = inspector.get_part('1234567890', {'par': 1})

        assert part == expected_part

        get_part.return_value = expected_part = Mock()


    def should_run_till_None_order(self):
        inspector = t.Inspector(Mock(), Mock(), 'loc')
        inspector.run_test = lambda order: time.sleep(0.1)

        inspector.start()
        assert inspector.state == 'waiting'
        inspector.orders.put('mock_order')
        time.sleep(0.05)
        assert inspector.state == 'iddle'
        assert inspector.orders.qsize() == 0
        time.sleep(0.05)

        assert inspector.state == 'waiting'
        inspector.orders.put(None)
        time.sleep(0.05)
        assert not inspector.is_alive()
        assert inspector.state == 'stopped'

    def should_stop(self):
        inspector = t.Inspector(Mock(), Mock(), 'loc')
        inspector.run_test = lambda order: time.sleep(0.1)

        inspector.start()
        inspector.orders.put('mock_order 1')
        inspector.orders.put('mock_order 2')
        inspector.orders.put('mock_order 3')

        time.sleep(0.1)
        orders = inspector.stop()
        assert inspector.orders.qsize() == 0
        assert len(orders) == 2
        time.sleep(0.1)
        assert not inspector.is_alive()

    def should_process_questions(self):
        inspector = t.Inspector(Mock(), Mock(), 'loc')
        question = inspector.ask('Do you want to live forever?')
        event = inspector.events.get()
        assert event == ('waiting', question)
        assert question == self.Question.return_value

    def should_run_test(self):
        db = Mock()
        dev_container = Mock()

        inspector = t.Inspector(db, dev_container, 'ĺoc')
        inspector.set_responsible = Mock()
        inspector.set_part_model = Mock()
        inspector.get_part = Mock()
        part = inspector.get_part.return_value
        control_plan = inspector.control_plan = Mock()

        part_info = {'part_number': 'part_number',
                     'serial_number': '1234567890'
        }

        inspector.run_test((part_info, 'resp'))

        inspector.set_responsible.assert_called_with('resp')
        inspector.set_part_model.assert_called_with('part_number')
        inspector.get_part.assert_called_with('1234567890', {})
        test = control_plan.implement.return_value

        test.start.assert_called_with(
            part=part, dev_container=dev_container,
            cavity=None, tff=inspector.tff
        )
        test.walk.assert_called_with()
        test.execute.assert_called_with()
        test.close.assert_called_with()
        db.Session().commit.assert_called_with()


class A_Question:
    def ask_question(self, question):
        question.ask('Are you?', 'bubilla?')

    def should_wait_till_answer(self):
        question = t.Question()
        thread = threading.Thread(target=self.ask_question,
                                  args=(question,))

        thread.start()
        assert thread.is_alive()

        question.answer('Yes, I am')
        time.sleep(0.1)

        assert not thread.is_alive()

        assert question.request == ('Are you?', 'bubilla?')
        assert question.response == ['Yes, I am']
