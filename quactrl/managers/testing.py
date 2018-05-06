import threading
from queue import Queue
from quactrl.domain.data import dal
from quactrl.managers.devices import DevManager
from quactrl.managers import Event


class TestManager:
    """Create  and manage testers"""
    def __init__(self):
        self.events = Queue()
        self.testers = []
        self.dev_manager = DevManager()
        self._location = None

    @property
    def tests(self):
        return [None if tester is None
                else tester.test
                for tester in self.testers]

    def set_database(self, connection_string):
        """Connects database"""
        dal.connect(connection_string)

    def go_to(self, location):
        """Load all devices from location"""
        self._location = location
        self.dev_manager.load_devs_from(location)

    def start_test(self, part_info, responsible, **test_pars):
        """Start test from part_information, responsible and other process parameters"""
        cavity = test_pars.pop('cavity', 1)
        # Amplified testers from cavity information

        tester = self._get_tester(cavity)
        tester.orders.put((part_info, responsible, test_pars))

    def _get_tester(self, cavity):
        if cavity > len(self.testers):
            for _ in range(cavity - len(self.testers)):
                self.testers.append(None)

        index = cavity - 1
        if self.testers[index] is None:
            tester = Tester(self._location, self.dev_manager, self.events)
            tester.start()
            self.testers[index] = tester

        return tester

    def stop(self, cavity=None):
        if cavity is None:
            for tester in self.testers:
                if tester:
                    tester.stop()
        else:
          tester = self.testers[cavity-1]
          if tester:
              tester.stop()


class Tester(threading.Thread):
    def __init__(self, location, dev_manager, events ):
        super().__init__()
        self.location = location
        self.dev_manager = dev_manager
        self.events = events
        self.orders = Queue()
        self.responsible = None
        self.stop_signal = False
        self.control_plan = None
        self._responsible = None

    def run(self):
        while not self.stop_signal:
            order = self.orders.get()
            if order is not None:
                self.process(order)

    def stop(self):
        self.stop_signal = True
        if self.orders.qsize() == 0:
            self.orders.put(None)

    def process(self, order):
        part_info, responsible_key, test_pars = order
        part = dal.get_or_create_part(part_info, location)

        self.set_responsible_by(responsible_key)
        self.set_control_plan_by(part, self.location)

        test = self.control_plan.get_test()
        test.part = part
        test.responsible = self.responsible

        self.events.put(Event('start', test))

        session = dal.Session()
        for check in test.checks:
            pass


#     class PushRunner(Thread):
    # def __init__(self, dal,  origin=None, destination=None,
    #              interrupt_event=None, controller=None, **path_args):
    #     super().__init__()

    #     self.dal = dal
    #     self.path_args = path_args

    #     self.interrupt_event = interrupt_event
    #     self.controller = controller

    #     self.devices = None
    #     self.method = None

    #     self.steps = None
    #     self.origin = Queue() if origin is None else origin
    #     self.destination = Queue() if destination is None else destination
    #     self.adapter = None
    #     self.path = None

    #     self.stop_cycle = False
    #     self.responsible_key = None

    # def path_is_loaded(self):
    #     return self.path is not None

    # def load_process(self):
    #     self.steps = []
    #     if self.path:
    #         self.method = MethodRepo.get(self.path.method_name)

    # def set_responsible_by_key(self, key):
    #     self.responsible_key = key

    # def _shall_interrupt(self):
    #     return (self.interrupt_event is not None and
    #             self.interrupt_event.is_set())

    # def _are_tokens(self, inputs):
    #     result = type(inputs) is list
    #     if result:
    #         for value in inputs:
    #             result = result and type(value) is int
    #     return result

    # def run(self):
    #     self.adapter = ProcessAdapter(self, self.dal, self.path_args)
    #     self.adapter.open()
    #     responsible = None
    #     while True:
    #         inputs = self.origin.get()

    #         # There are external orders to stop thread
    #         if inputs is None or self._shall_interrupt():  # thread is finished
    #             break

    #         if responsible is None or (
    #                 responsible.key != self.responsible_key):
    #             responsible = self.adapter.get_person(self.responsible_key)
    #         if responsible is None:
    #                 self._notify_error('AbsentResponsible')
    #         else:
    #             if self._are_tokens(inputs): # list of integers
    #                 in_tokens = self.adapter.get_tokens_by_ids(inputs)
    #                 inputs = []
    #             else:
    #                 in_tokens = []
    #                 inputs = [inputs]

    #             if (self.path is None or
    #                    not self.path.accept_inputs(inputs)):
    #                 self.path = self.adapter.get_path(inputs)
    #                 self.path.devices = self.adapter.get_devices()
    #                 self.load_process()

    #             if self.path is None:
    #                 self._notify_error('IncorrentOperationInputs',
    #                                              inputs=inputs)
    #             else:

    #                 self.flow = self.path.create_flow(responsible,
    #                                                   self.controller)
    #                 self.flow.inputs = inputs
    #                 self.flow.in_tokens = in_tokens
    #                 self.adapter.add(self.flow)
    #                 self.flow.prepare()

    #                 self._update(self.flow)
    #                 cancel = self.stop_cycle
    #                 if self.flow.children:
    #                     for step in self.flow.children:
    #                         step.prepare()
    #                         self._update(step)
    #                         if cancel:
    #                             step.cancel()
    #                         else:
    #                             try:
    #                                 step.execute()
    #                                 step.terminate()
    #                             except Exception as e:
    #                                 cancel = True
    #                                 step.cancel()
    #                                 self._notify_error(e, step=step)
    #                         self._update(step)

    #                         if self._shall_interrupt():
    #                             cancel = True
    #                         if self.stop_cycle:
    #                             cancel = True
    #                             self.stop_cycle = False
    #                 if cancel:
    #                     self.flow.cancel()
    #                 else:
    #                     self.flow.execute()
    #                     self.flow.terminate()
    #                 self.adapter.commit()
    #                 self._update(self.flow)
    #                 if self._shall_interrupt():
    #                     break
    #                 self.destination.put([token.id
    #                                       for token in self.flow.out_tokens])
    #     self.adapter.close()

    # def cancel_cycle(self):
    #     self.stop_cycle = True

    # def _notify(self, message_key, *obj):
    #     if self.controller:
    #         self.controller.notify(message_key, *obj)

    # def _notify_error(self, message_key, **kwargs):
    #     if self.controller:
    #         self.controller.notify_error(message_key, **kwargs)

    # def _update(self, obj):
    #     if self.controller:
    #         self.controller.update(obj)
