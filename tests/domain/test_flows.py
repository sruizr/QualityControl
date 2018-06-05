from unittest.mock import Mock
from queue import Queue
import quactrl.domain.flows as f
import quactrl.domain.items as i
import quactrl.domain.paths as p
import quactrl.domain.base as b
from tests.domain import EmptyDataTest


class A_Creation:
    def should_create_token_on_destination(self):
        resource = b.Resource(key='resource')
        item = b.Item(resource)
        responsible = b.Node(key='responsible')
        destination = b.Node(key='destination')

        creation = f.Creation(responsible)

        item.qty = 2.0
        creation.run(destination, item)

        assert item.avalaible_tokens[0].qty == 2.0
        assert item.avalaible_tokens[0].node == destination
        assert item.avalaible_tokens[0].producer == creation.operations[0]

class A_Destruction:
    def should_remove_token_on_origin(self):
        resource = b.Resource(key='resource')
        item = b.Item(resource)
        responsible = b.Node(key='responsible')
        origin = b.Node(key='origin')
        fake_op = Operation()

        item.avalaible_tokens.append(
            b.Token(node=origin, producer=fake_op, qty=2.0))


        # destruction = f.Destruction(responsible)

        # item.qty = 1.0
        # destruction.run(origin, item)

        # assert item.avalaible_tokens[0].qty == 2.0
        # assert item.avalaible_tokens[0].node == destination
        # assert item.avalaible_tokens[0].producer == creation.operations[0]




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
