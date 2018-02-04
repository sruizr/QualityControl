from threading import Thread, Event
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


class OneItemFlowService:
    def __init__(self, environment):
        super().__init__()
        dal = environment.dal

        self.interrupt_event = Event()
        self.controller = environment.controller
        self.main_queue = Queue()
        self.generator = PullRunner(destination=self.main_queue,
                                    interrupt_event=self.interrupt_event
                                    )
        self.generator.adapter = ProcessAdapter(
            self.generator, dal,
            to_node_key=environment.location_key,
            from_node=None
            )

        self.operation = PullRunner(origin=self.main_queue,
                                    controller=self.controller,
                                    interrupt_event=self.interrupt_event
                                    )
        self.operation.adapter = ProcessAdapter(
            self.operation, dal,
            from_node_key=environment.location_key,
            name=environment.operation_name
            )

    def enter_item(self, item_data, responsible_key):
        inputs = self.operation.adapter.find_inputs(item_data)
        if not inputs:
            self.generator.origin.put(item_data, responsible_key)
        else:
            for _input in inputs:
                self.operation.source.put((_input, responsible))

    def start(self):
        if self.generator.path_is_loaded():
            self.generator.start()
        self.operation.start()

    def stop(self):
        self.operation.origin.put(None)
        self.generator.origin.put(None)

    def interrupt(self):
        self.interrupt_event.set()

    def stop_cycle(self):
        self.operation.stop_cycle()


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
    def __init__(self, origin=None, destination=None, interrupt_event=None,
                 controller=None):
        super().__init__()
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
        self.responsible = None

    def path_is_loaded(self):
        return self.path is not None

    def load_process(self):
        self.steps = []
        if self.path:
            self.method = MethodRepo.get(self.path.method_name)
            for sub_path in self.path.children:
                self.steps.append(StepRunner(sub_path))

    def run(self):
        self.adapter.open()
        while True:
            import pdb; pdb.set_trace()
            _input = self.origin.get()
            if _input is None or (
                    self.interrupt_event is not None and
                    self.interrupt_event.is_set()
                    ):  # thread is finished
                break
            import pdb; pdb.set_trace()
            inputs, responsible_key = _input
            if (self.path is None or
                    not self.path.accept_inputs(inputs)):
                self.adapter.set_path(inputs)
                self.load_process()

            if (self.responsible is None or
                    responsible_key != self.responsible.key):
                self.responsible = self.adapter.get_person(responsible_key)

            if self.path is None:
                self.controller.notify_error(IncorrectOperationInputs(),
                                             inputs=inputs)
            else:
                self.flow = Flow(self.path, self.responsible, self.controller)
                self.flow.inputs = inputs
                self.adapter.add(self.flow)
                self.flow.prepare()
                if self.flow.children:
                    for step in self.steps:
                        step.prepare()
                        step.execute()
                        step.terminate()
                        if (self.interrupt_event is not None and
                                self.interrupt_event.is_set()):
                            self.flow.cancel()
                            self.adapter.commit()
                            break
                        if self.stop_cycle:
                            self.flow.cancel()
                            self.stop_cycle = False
                            self.adapter.commit()

                self.flow.execute()
                tokens = self.flow.terminate()
                self.adapter.commit()
                for token in tokens:
                    self.destination.put(token.encode())
                self.controller.notify('cycle_finished', self.path)
        self.adapter.close()

    def cancel_cycle(self):
        self.stop_cycle = True


class ProcessAdapter:
    """Adapter between dinamic ProcessRunner and Static Path on Domain"""
    def __init__(self, process_runner, dal, **path_args):
        self.process_runner = process_runner
        self.dal = dal
        self.path_args = path_args
        self._session = None

    def set_path(self, in_items=None):
        """Load a path compatible with the in_items, return None otherwise"""

        self.process_runner.path = self.dal.plan.get_path(self.path_args,
                                                          self._session)
        self.process_runner.devices = self.dal.do.get_devices_by_location(
            self.process_runner.path.from_node, self._session
            )

    def find_inputs(self, item_args):
        inputs = self.dal.do.get_avalaible_inputs(
            self.path_args['from_node_key'], item_args, self._session
        )
        return inputs

    def get_person(self, key):
        return self.dal.do.get_person(key, self._session)

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
