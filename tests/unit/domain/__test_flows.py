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
