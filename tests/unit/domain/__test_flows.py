from queue import Queue
from threading import Thread, Event
import quactrl.domain.flows as f
import quactrl.domain.items as i
import quactrl.domain.base as b
import quactrl.domain.resources as r
import quactrl.domain.paths as p
from tests.domain import EmptyDataTest
from unittest.mock import Mock, call, patch


class A_Creation(EmptyDataTest):
    def should_create_token_on_destination(self):
        resource = b.Resource()
        item = b.Item()
        item.resource = resource
        responsible = b.Node()
        destination = b.Node()

        creation = f.Creation(responsible)

        item.qty = 2.0
        creation.run(destination, item)

        self.session.add(creation)
        # self.session.add(item)
        self.session.commit()

        assert item.avalaible_tokens[0].qty == 2.0
        assert item.avalaible_tokens[0].node == destination
        assert item.avalaible_tokens[0].producer == creation


class A_Destruction(EmptyDataTest):
    def should_remove_token_on_origin(self):
        resource = b.Resource()
        item = b.Item()
        item.resource = resource
        responsible = b.Node()
        origin = b.Node()
        item.avalaible_tokens.append(
            b.Token(item=item, node=origin, qty=2.0))

        destruction = f.Destruction(responsible)

        item.qty = 1.0
        destruction.run(origin, item)

        self.session.add(destruction)
        # self.session.add(item)
        self.session.commit()

        assert len(item.avalaible_tokens) == 1
        assert item.avalaible_tokens[0].qty == 1.0
        assert item.avalaible_tokens[0].node == origin
        assert item.avalaible_tokens[0].producer == None
        assert item.avalaible_tokens[0].consumer == None

class A_Movement(EmptyDataTest):
    def should_move_items(self):
        resource = b.Resource()
        item = b.Item()
        item.resource = resource
        responsible = b.Node()
        origin = b.Node()
        destination = b.Node()
        item.avalaible_tokens.append(
            b.Token(item=item, node=origin, qty=2.0))

        movement = f.Movement(responsible)
        item.qty = 1.0
        movement.run(origin, destination, item)

        self.session.add(movement)
        self.session.commit()

        assert len(item.avalaible_tokens) == 2
        assert item.avalaible_tokens[0].qty == 1.0
        assert item.avalaible_tokens[0].node == destination
        assert item.avalaible_tokens[1].qty == 1.0
        assert item.avalaible_tokens[1].node == origin

# class A_Test:
#     def should_prepare(self):
#         part = Mock()
#         events_queue = Queue()
#         observer = Mock()
#         cancel_signal = False

#         test = f.Test()
#         test.prepare(
#             part=part,
#             events=events_queue,
#             observer=observer,
#             cancel_signal = cancel_signal
#         )

#         assert test.part == part
#         assert test.events == events_queue
#         assert test.observer == observer
#         assert part in test.inputs
#         assert part in test.outputs



# class A_Test(EmptyDataTest):
#     def should_store_diferent_operations(self):
#         test = f.Test()
#         basic = f.BasicOp(sequence=0, flow=test)
#         check = f.Check(sequence=5, flow=test)

#         self.session.add(test)
#         self.session.add(basic)
#         self.session.add(check)
#         self.session.commit()

#         assert len(test.operations) == 2

#         del test
#         del basic
#         del check

#         added_test = self.session.query(f.Test).first()
#         assert added_test.operations[0].my_method()
#         assert added_test.operations[1].other_method()


class CheckRunner(Thread):
    def __init__(self, check):
        super().__init__()
        self.check = check
        self.check.thread = Mock()

    def run(self):
        self.check.run()


class A_Check:
    def should_run_sync_check(self):
        test = f.Test()
        test.notify = Mock()
        test.part = Mock()

        check = f.Check()
        check.test = test
        check.run()

        assert test.notify.mock_calls == [call(check)] * 2
        assert check.state == 'ok'

    def should_run_async_check(self):

        test = f.Test()
        test.part = Mock()
        test.notify = Mock()
        check = f.Check()
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
        assert test.notify.mock_calls == [call(check)] * 3

    def should_cancel_async_check_running(self):
        test = f.Test()
        test.part = Mock()
        test.notify = Mock()

        check = f.Check()
        check.test = test
        check.finish = Mock()

        check_runner = CheckRunner(check)
        check_runner.start()

        check.cancel()
        while check_runner.is_alive():
            pass

        assert check.state == 'cancelled'
        assert test.notify.mock_calls == [call(check)] * 3
        check.thread.cancel.assert_called_with()


class A_CheckWithHelpers(EmptyDataTest):
    def should_add_new_measures(self):
# <<<<<<< HEAD
#         check = f.Check()
#         part = i.Part(resourc)


#         value =2.0
#         characteristic = r.Characteristic('characteristic')
#         element_key = 'e_key'
#         check.add_measure(value, characteristic, element_key)

#         part = check.test.part
#         assert part
# =======
        model = r.PartModel()
        part = i.Part()
        part.part_model = model
        characteristic = r.Characteristic()
        check = f.Check()
        check.part = part
        check.outputs = []

        check.add_measure(2.0, characteristic, element_key='el_1')

        assert len(part.measurements) == 1
        measurement = part.measurements[0]
        assert measurement.qty == 2.0
        assert measurement.characteristic == characteristic
        assert measurement == check.outputs[0]

# >>>>>>> 6ca63ab1be90bcb96a3efab5df7e3116d40225f5

    def should_replace_old_measures(self):
        part = i.Part()
        characteristic = r.Characteristic(key='char')
        check = f.Check()
        check.part = part
        part.tracking = '1234'
        check.outputs = []

        i.Measurement(part, characteristic, tracking='1234*char[el_1]')

        check.add_measure(2.0, characteristic, element_key='el_1')

        assert len(part.measurements) == 1
        measurement = part.measurements[0]
        assert measurement.qty == 2.0
        assert measurement.characteristic == characteristic
        assert measurement == check.outputs[0]


    def should_add_new_defects(self):
        failure_mode = r.FailureMode(r.Characteristic(key='char'), 'low')
        check = f.Check()
        part = i.Part()
        part.tracking = '1234'
        check.part = part
        check.outputs = []

        defect = check.add_defect(failure_mode, element_key='el_1', qty=2.0)

        assert len(part.defects) == 1
        assert defect == part.defects[0]
        assert defect.qty == 2.0
        assert defect.tracking == '1234*low-char[el_1]'
        assert defect.failure_mode == failure_mode
        assert defect == check.outputs[0]

    def should_add_old_defects(self):
        failure_mode = r.FailureMode(r.Characteristic(key='char'), 'low')
        part = i.Part()
        part.tracking = '1234'
        check = f.Check()
        check.part = part
        check.outputs = []

        defect = i.Defect(part, failure_mode)
        defect.tracking = '1234*low-char[el_1]'

        new_defect = check.add_defect(failure_mode, element_key='el_1', qty=2.0)

        assert len(part.defects) == 1
        assert defect == part.defects[0]
        assert new_defect == defect
        assert defect.qty == 2.0
        assert defect.tracking == '1234*low-char[el_1]'
        assert defect.failure_mode == failure_mode
        assert defect == check.outputs[0]


    def should_clean_old_defects(self):
        control = p.Control()
        source_check = f.Check()
        check = f.Check()
        check.inputs = []
        check.control = source_check.control = control
        failure_mode = r.FailureMode(r.Characteristic(key='char'), 'low')

        part = i.Part()
        check.part = part
        defect = i.Defect(part, failure_mode)
        defect.avalaible_tokens.append(
            b.Token(item=defect, qty=1.0, producer=source_check)
            )

        check.clean_old_defects()

        assert defect in check.inputs
        assert defect.qty == None


    def should_track_devices(self):
        devices = [Mock(tracking='{}'.format(i)) for i in range(3)]

        check = f.Check()

        check.track_devices(*devices)

        assert check.tracking == '0&1&2'
