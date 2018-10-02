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
        self.service = t.TestingService(self.db)

    def should_setup_without_cavities(self):
        serv = self.service

        serv.setup('loc', till_first_failure=False)
        assert serv.cavities == 1
        assert serv.active_cavities == [None]
        self.Inspector.assert_called_with(
            serv.db, serv.dev_container, 'loc',  None, False
        )
        inspector = self.Inspector.return_value
        inspector.start.assert_called_with()

    def should_setup_with_all_cavities(self):
        serv = self.service

        serv.setup('loc', 5)

        assert serv.cavities == 5
        for cavity in range(5):
            assert cavity in serv.inspectors.keys()

    def should_setup_with_some_cavities(self):
        serv = self.service

        serv.setup('loc', [2, 3])

        assert serv.cavities == 2
        for cavity in [2, 3]:
            assert cavity in serv.inspectors.keys()

    def should_raise_exception_when_there_are_inspectors_working(self):
        serv = self.service

        serv.inspectors = {1: Mock()}
        try:
            serv.setup('lock')
            pytest.fail('No InspectorException raised')
        except t.InspectorException:
            pass

    def should_stack_test_on_cavity(self):
        serv = self.service
        inspector = Mock()
        serv.inspectors = {1: inspector}

        serv.stack_test('part_info', 'responsible_key', 1)

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
            'quactrl.services.testing.Question'
        ])

    def should_have_correct_name(self):
        inspector = t.Inspector(Mock(), Mock(), 'loc')
        assert inspector.name == 'Inspector'

        inspector = t.Inspector(Mock(), Mock(), 'loc', cavity=7)
        assert inspector.name == 'Inspector_7'

    def should_set_responsible(self):
        db = Mock()
        inspector = t.Inspector(db, Mock(), 'loc')
        responsible = db.Persons().get_by_key.return_value

        inspector.set_responsible('responsible')

        assert responsible == inspector.responsible

        inspector.set_responsible('other')
        assert db.Persons().get_by_key.call_count == 2
        db.Persons().get_by_key.assert_called_with('other')

    def should_set_route(self):
        db = Mock()
        inspector = t.Inspector(db, Mock(), 'loc')
        get_part_model = db.PartModels().get_by_part_number
        get_route = db.Routes().get_by_part_model_and_location

        inspector.set_route_for('part_number')
        assert inspector.part_model == get_part_model.return_value
        assert inspector.route == get_route.return_value

        get_part_model.assert_called_with('part_number')
        get_route.assert_called_with(inspector.part_model,
                                     db.Locations().get_by_key.return_value)

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
        inspector.set_route_for = Mock()
        route = inspector.route = Mock()

        part_info = {'part_number': 'part_number'}
        part = db.Parts().get_or_create.return_value

        inspector.run_test((part_info, 'resp'))

        inspector.set_responsible.assert_called_with('resp')
        inspector.set_route_for.assert_called_with(part)
        test = route.create_operation.return_value

        test.start.assert_called_with(
            subject=part, dev_container=dev_container,
            cavity=None, tff=inspector.tff,
            update=inspector.update
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
