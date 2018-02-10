from threading import Thread, Event, get_ident
from queue import Queue
from quactrl.domain import get_component
from quactrl.domain.check import Test
from quactrl.domain.erp import Flow


class InsertItemError(Exception):
    pass


class IncorrectOperationInputs(Exception):
    pass


class MethodError(Exception):
    pass



class MethodRepo:
    _methods = {}

    @classmethod
    def get(cls, key):
        if key not in cls._methods:
            method = get_component(key)
            if method is None:
                return None
            cls._methods[key] = method

        return cls._methods[key]


class PullRunner(Thread):
    def __init__(self, dal,  origin=None, destination=None,
                 interrupt_event=None, controller=None, **path_args):
        super().__init__()

        self.dal = dal
        self.path_args = path_args

        self.interrupt_event = interrupt_event
        self.controller = controller

        self.devices = None
        self.method = None

        self.steps = None
        self.origin = Queue() if origin is None else origin
        self.destination = Queue() if destination is None else destination
        self.adapter = None
        self.path = None

        self.stop_cycle = False
        self.responsible_key = None

    def path_is_loaded(self):
        return self.path is not None

    def load_process(self):
        self.steps = []
        if self.path:
            self.method = MethodRepo.get(self.path.method_name)

    def set_responsible_by_key(self, key):
        self.responsible_key = key

    def _shall_interrupt(self):
        return (self.interrupt_event is not None and
                self.interrupt_event.is_set())

    def _are_tokens(self, inputs):
        result = type(inputs) is list
        if result:
            for value in inputs:
                result = result and type(value) is int
        return result

    def run(self):
        self.adapter = ProcessAdapter(self, self.dal, self.path_args)
        self.adapter.open()
        responsible = None
        while True:
            inputs = self.origin.get()

            # There are external orders to stop thread
            if inputs is None or self._shall_interrupt():  # thread is finished
                break

            if responsible is None or (
                    responsible.key != self.responsible_key):
                responsible = self.adapter.get_person(self.responsible_key)
            if responsible is None:
                    self._notify_error('AbsentResponsible')
            else:
                if self._are_tokens(inputs): # list of integers
                    in_tokens = self.adapter.get_tokens_by_ids(inputs)
                    inputs = []
                else:
                    in_tokens = []
                    inputs = [inputs]

                if (self.path is None or
                       not self.path.accept_inputs(inputs)):
                    self.path = self.adapter.get_path(inputs)
                    self.path.devices = self.adapter.get_devices()
                    self.load_process()

                if self.path is None:
                    self._notify_error('IncorrentOperationInputs',
                                                 inputs=inputs)
                else:

                    self.flow = self.path.create_flow(responsible,
                                                      self.controller)
                    self.flow.inputs = inputs
                    self.flow.in_tokens = in_tokens
                    self.adapter.add(self.flow)
                    self.flow.prepare()

                    self._update(self.flow)
                    cancel = self.stop_cycle
                    if self.flow.children:
                        for step in self.flow.children:
                            step.prepare()
                            self._update(step)
                            if cancel:
                                step.cancel()
                            else:
                                try:
                                    step.execute()
                                    step.terminate()
                                except Exception as e:
                                    cancel = True
                                    step.cancel()
                                    self._notify_error(e, step=step)
                            self._update(step)

                            if self._shall_interrupt():
                                cancel = True
                            if self.stop_cycle:
                                cancel = True
                                self.stop_cycle = False
                    if cancel:
                        self.flow.cancel()
                    else:
                        self.flow.execute()
                        self.flow.terminate()
                    self.adapter.commit()
                    self._update(self.flow)
                    if self._shall_interrupt():
                        break
                    self.destination.put([token.id
                                          for token in self.flow.out_tokens])
        self.adapter.close()

    def cancel_cycle(self):
        self.stop_cycle = True

    def _notify(self, message_key, *obj):
        if self.controller:
            self.controller.notify(message_key, *obj)

    def _notify_error(self, message_key, **kwargs):
        if self.controller:
            self.controller.notify_error(message_key, **kwargs)

    def _update(self, obj):
        if self.controller:
            self.controller.update(obj)


class ProcessAdapter:
    """Adapter between dinamic ProcessRunner and Static Path on Domain"""
    def __init__(self, process_runner, dal, path_args):
        self.process_runner = process_runner
        self.dal = dal
        self.path_args = path_args
        self._session = None

    def get_path(self, in_items=None):
        """Load a path compatible with the in_items, return None otherwise"""

        return  self.dal.plan.get_path(self.path_args,
                                                       self._session)

    def get_devices(self):
        return  self.dal.do.get_devices_by_location(
            self.process_runner.path.from_node.key, self._session
            )

    def find_inputs(self, item_args):
        inputs = self.dal.do.get_avalaible_inputs(
            self.path_args['from_node_key'], item_args, self._session
        )
        return inputs

    def get_person(self, key):
        return self.dal.do.get_person(key, self._session)

    def get_tokens_by_ids(self, token_ids):
        return self.dal.do.get_tokens_by_ids(token_ids, self._session)

    def open(self):
        self._session = self.dal.Session()

    def add(self, obj):
        self._session.add(obj)

    def commit(self):
        self._session.commit()

    def close(self):
        self._session.close()
