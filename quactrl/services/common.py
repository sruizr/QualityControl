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
        if self.responsible_key is None: # Not allowed any flow without responsible
            self._notify_error('AbsentResponsible')
        responsible = self.adapter.get_person(self.responsible_key)
        while True:
            inputs = self.origin.get()

            # There are external orders to stop thread
            if inputs is None or self._shall_interrupt():  # thread is finished
                break

            if responsible is None: # Not allowed any flow without responsible
                self._notify_error('AbsentResponsible')
            else:
                if responsible.key != self.responsible_key:
                    responsible = self.adapter.get_person(self.responsible_key)

                if self._are_tokens(inputs): # list of integers
                    inputs = self.adapter.get_tokens_by_ids(inputs)
                else:
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

                    self.flow = self.path.create_flow(responsible, self.controller)
                    self.flow.inputs.extend(inputs)
                    self.adapter.add(self.flow)
                    self.flow.prepare()
                    self._notify('cycle_started', self.flow)
                    if self.flow.children:
                        for step in self.flow.childrens:
                            step.prepare()
                            self._notify('step_started', step)
                            step.execute()
                            step.terminate()
                            self._notify('step_finished', step)
                            if self._shall_interrupt():
                                self.flow.cancel()
                                self.adapter.commit()
                                self._notify('cycle_cancelled', self.flow)
                                break
                            if self.stop_cycle:
                                self.flow.cancel()
                                self.adapter.commit()
                                self.stop_cycle = False
                                self._notify('cycle_cancelled', self.flow)

                    self.flow.execute()
                    self.flow.terminate()
                    self.adapter.commit()
                    self.destination.put([token.id
                                          for token in self.flow.out_tokens])
                    self._notify('cycle_finished', self.path)

        self.adapter.close()

    def cancel_cycle(self):
        self.stop_cycle = True

    def _notify(self, message_key, *obj):
        if self.controller:
            self.controller.notify(message_key, *obj)

    def _notify_error(self, message_key, **kwargs):
        if self.controller:
            self.controller.notify_error(message_key, **kwargs)


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


class StepRunner:
    """Sync version of path"""
    def __init__(self, path):
        self.path = path
        self.method = MethodRepo.get(self.method_name)

    def execute(self, in_resources, responsible, devices, controller=None):
        if self.method:
            self.path.prepare()
            self.method(self.path, in_resources, devices, controller)
            self.path.terminate(responsible)
