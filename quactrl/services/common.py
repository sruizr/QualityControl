from threading import Thread, Event
from queue import Queue


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

    def enter_item(self, item_data, responsible):
        tokens = self.operation.adapter.get_tokens(item_data)
        if tokens is None:
            if self.generator.is_loaded():
                self.generator.origin.put(((item_data, 1.0), responsible))
            else:
                self.controller.notify_error(
                    InsertItemError(),
                    item_data
                    )
        else:
            self.operation.source.put((tokens, responsible))

    def start(self):
        if self.generator.is_loaded():
            self.generator.start()
        self.operation.start()

    def stop(self):
        self.operation.origin.put(None)
        if self.generator.has_path():
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
        while True:
            _input = self.origin.get()
            if _input is None or (
                    self.interrupt_event is not None and
                    self.interrupt_event.is_set()
                    ):  # thread is finished
                break
            in_tokens, responsible_key = _input
            if (self.path is None or
                    not self.path.accept_tokens(in_tokens)):
                self.adapter.set_path(in_tokens)
                self.load_process()

            if (self.responsible is None or
                    responsible_key != self.responsible.key):
                self.responsible = self.adapter.get_person(responsible_key)

            if self.path is None:
                self.notify_error(IncorrectOperationInputs(), tokens=in_tokens)
            else:
                self.path.prepare()
                if self.path.children:
                    for step in self.steps:
                        step.execute(in_tokens, self.responsible, controller=self.controller)
                        if (self.interrupt_event is not None and
                                self.interrupt_event.is_set()):
                            self.path.cancel(self.responsible)
                            self.adapter.commit()
                            break
                        if self.stop_cycle:
                           self.path.cancel(self.responsible)
                           self.stop_cycle = False
                           self.adapter.commit()

                self.execute(in_tokens)
                self.destination.put(self.path.out_tokens)
                self.path.terminate(self.responsible)
                self.controller.notify('cycle_finished', self.path)
            self.adapter.commit()
        self.adapter.close()

    def execute(self, in_tokens):
        if self.method:
            self.method(self.path, in_tokens, self.controller)

    def cancel_cycle(self):
        self.stop_cycle = True


class ProcessAdapter:
    """Adapter between dinamic ProcessRunner and Static Path on Domain"""
    def __init__(self, process_runner, dal, **path_args):
        self.process_runner = process_runner
        self.dal = dal
        self.session = self.process_runner.session
        self.path_args = path_args
        self._session = self.dal.Session()

    def set_path(self, in_items):
        """Load a path compatible with the in_items, return None otherwise"""
        self.process_runner.path = self.dal.plan.get_path(self.path_args, self.session)
        self.process_runner.path.devices = self.dal.do.get_devices_by_location(
            self.process_runner.path.from_node
            )

    def find_inputs(self, **item_args):
        inputs = self.dal.plan.get_avalaible_tokens(self.path.from_node.key,
                                                    item_args, self.session)
        return inputs

    def get_person(self, key):
        return self.dal.do.get_person(key, self.session)

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
