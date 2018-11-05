from unittest.mock import Mock
import time
from ...units import TestWithPatches
import threading
import quactrl.services.testing as t
import pytest


@pytest.mark.current
class A_TestingService(TestWithPatches):
    def setup_method(self, method):
        super().create_patches([
            'quactrl.services.testing.Inspector',
            'quactrl.services.testing.DeviceContainer'
        ])
        self.db = Mock()
        self.service = t.Service(self.db, 'location')

    def should_init_with_dev_container(self):
        serv = t.Service(self.db, 'location')

        assert serv.cavities == 0
        assert not serv.active_cavities

        dev_repo = self.db.Devices.return_value
        dev_repo.get_all_from.assert_called_with('location')
        self.DeviceContainer.assert_called_with(
            dev_repo.get_all_from.return_value
        )

    def should_start_a_cavity(self):
        serv = t.Service(self.db, 'location')

        serv.start(1)
        assert serv.cavities == 1
        assert serv.active_cavities == [1]
        self.Inspector.assert_called_with(
            self.db, self.DeviceContainer.return_value,
            'location', 1, True
        )

        serv.restart = Mock()
        serv.start(1)

        serv.restart.assert_called_with(1)

    def should_start_many_cavities(self):
        serv = t.Service(self.db, 'location')

        serv.start([1, 3, 5])
        assert serv.cavities == 3
        assert set(serv.active_cavities) == set([1, 3, 5])

    def should_stop_a_cavity(self):
        serv = t.Service(self.db, 'location')

        serv.inspectors[1] = inspector_1 = Mock()

        pending_orders = serv.stop(1)

        assert 1 not in serv.inspectors
        inspector_1.stop.assert_called_with()
        assert pending_orders == inspector_1.stop.return_value

    def should_stop_all_cavities(self):
        serv = t.Service(self.db, 'location')

        serv.inspectors[1] = inspector_1 = Mock()
        serv.inspectors[3] = inspector_3 = Mock()

        pending_orders = serv.stop()

        assert not serv.inspectors
        inspector_1.stop.assert_called_with()
        inspector_3.stop.assert_called_with()
        assert pending_orders[1] == inspector_1.stop.return_value
        assert pending_orders[3] == inspector_3.stop.return_value

    def should_restart_a_cavity_reinserting_orders(self):
        serv = t.Service(self.db, 'location')
        serv.inspectors[1] = Mock()

        serv.start = Mock()
        serv.stop = Mock()
        serv.stop.return_value = ['order']

        result = serv.restart(1)

        serv.stop.assert_called_with(1)
        serv.start.assert_called_with(1)
        serv.inspectors[1].orders.put.assert_called_with('order')
        assert result is None

    def should_restart_a_cavity_returning_orders(self):
        serv = t.Service(self.db, 'location')
        serv.inspectors[1] = Mock()

        serv.start = Mock()
        serv.stop = Mock()
        serv.stop.return_value = ['order']

        result = serv.restart(1, False)

        serv.stop.assert_called_with(1)
        serv.start.assert_called_with(1)
        serv.inspectors[1].orders.put.assert_not_called()
        assert result == ['order']

    def should_restart_all_cavities(self):
        serv = t.Service(self.db, 'location')
        serv.inspectors[1] = Mock()
        serv.inspectors[4] = Mock()

        serv.start = Mock()
        serv.stop = Mock()
        serv.stop.return_value = ['order']

        serv.restart()

        assert len(serv.stop.mock_calls) == 2
        assert len(serv.start.mock_calls) == 2

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

    def should_return_last_events(self):
        pass

    def should_return_all_events(self):
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
