import time
from threading import Thread, Event, Timer
from queue import Queue
from quactrl.domain.check import Test, Check
from quactrl.domain import get_component
from quactrl.services.common import ProcessAdapter, PullRunner


class OneItemFlowService:
    def __init__(self, environment):
        super().__init__()
        dal = environment.dal


        self.interrupt_event = Event()
        self.controller = environment.controller
        self.controller.service = self
        self.location_key = environment.origin_key
        self.destination_key = environment.destination_key
        self.main_queue = Queue()
        self.generator = PullRunner(
            dal, destination=self.main_queue,
            controller=self.controller,
            interrupt_event=self.interrupt_event,
            from_node_key='wip',
            to_node_key=self.location_key
        )

        self.operation = PullRunner(
            dal, origin=self.main_queue,
            controller=self.controller,
            interrupt_event=self.interrupt_event,
            from_node_key=self.location_key,
            to_node_key=self.destination_key
        )
        self.dal = dal
        self.responsible_key = None

    def enter_item(self, item_data, responsible_key):

        if (self.responsible_key is None or
                self.responsible_key != responsible_key):
            self.operation.set_responsible_by_key(responsible_key)
            self.generator.set_responsible_by_key(responsible_key)

        token_ids = self.dal.do.get_avalaible_token_ids(
            location_key=self.location_key, item_args=item_data)

        if token_ids:
            self.operation.origin.put(token_ids)
        else:
            self.generator.origin.put(item_data)

    def start(self):
        self.generator.start()
        self.operation.start()

    def stop(self):
        self.generator.origin.put(None)
        while self.generator.is_alive():
            pass

        self.operation.origin.put(None)

    def interrupt(self):
        self.interrupt_event.set()

    def stop_cycle(self):
        self.operation.stop_cycle()
