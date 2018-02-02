import time
from threading import Thread, Event, Timer
from queue import Queue
from quactrl.domain.check import Test, Check
from quactrl.domain import get_component
import pdb


class InsertPartError(Exception):
    pass


class IncorrectOperationInputs(Exception):
    pass

class MethodError(Exception):
    pass


class OnePieceFlowService:
    def __init__(self, environment):
        super().__init__()
        self.controller = environment.controller
        dal = environment.dal
        self.responsible = None

        self.location = LocationQueue(environment.location_key,
                                      dal,
                                      self.controller
                                      )

        self.stop_event = Event()
        self.generator = Generator(dal,
                                   destination=self.location,
                                   stop_event=self.stop_event
                                   )
        self.operation = PullRunner(dal,
                                    method_name=environment.operation_name,
                                    origin=self.location,
                                    controller=self.controller,
                                    stop_event=self.stop_event
                                    )
        self.dal = dal

    def enter_part(self, part_data, responsible):
        if self.responsible is None or self.responsible.key != responsible:
            self.responsible = self.dal.do.get_person(responsible)

        if not self.location.try_load(part_data):
            if self.generator.is_loaded():
                self.generator.origin.put((part_data, self.responsible))
            else:
                self.controller.notify_error(
                    InsertPartError(),
                    **part_data
                    )

    def start(self):
        if self.generator.is_loaded():
            self.generator.start()
        self.operation.start()

    def stop(self):
        self.location.put(None)
        self.stop_event.set()


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


class ProcessRunner(Thread):

    def __init__(self, dal, stop_event=None, controller=None):
        super().__init__()
        self.dal = dal
        self.stop_event = stop_event
        self.controller = controller

        self.devices = None
        self.process = None
        self.method = None

        self.steps = None
        self.origin = None
        self.destination = None

    def is_loaded(self):
        return self.process is not None

    def set_process(self, in_resources=None):
        """This process should be overloaded"""
        self.process = None

    def load_process(self, in_resources):
        self.process = self.get_process(in_resources)
        self.steps = []
        if self.process:
            self.method = MethodRepo.get(self.process.method_name)
            if self.origin is None or self.origin.location != self.process.from_node:
                self.origin = LocationQueue(self.process.from_node)
            if self.destination is None or self.destination.location != self.process.to_node:
                self.destination = LocationQueue(self.process.to_node)
            if self.process.children:
                self.steps.append(StepRunner())

    def run(self):
        self.dal.open_session()
        while True:
            _input = self.origin.get()
            print(_input)
            if _input is None or (
                    self.stop_event is not None and self.stop_event.is_set()
                    ):  # thread is finished
                break
            in_items, responsible = _input
            in_resources = [item.resource for item in in_items]
            if (self.process is None or
                    not self.process.accept_inputs(in_resources)):
                self.load_process(in_resources)

            if self.process is None:
                self.notify_error(IncorrectOperationInputs(), in_items)
            else:
                if self.process.children:
                    for step in self.steps:
                        step.execute(in_items)
                        if (self.stop_event is not None and
                                self.stop_event.is_set()):
                            self.dal.commit_session()
                            break
                self.execute(in_items)
                self.destination.put(self.process.out_items)
                self.process.close(responsible)
                self.controller.notify_process_finished(self.process)
            self.dal.commit_session()

    def execute(self, in_resources):
        if self.method:
            self.method(self.process, in_resources, self.devices,
                        self.controller)


class PullRunner(ProcessRunner):

    def __init__(self, dal, origin, name, destination=None,
                 controller=None, stop_event=None):
        super().__init__(dal, stop_event=stop_event, controller=controller)

        self.origin = origin
        self.destination = destination
        if self.origin is None and self.destination is None:
            raise Exception('Node information is required')

        self.devices = self.dal.do.get_devices_by_location(
            self.origin.location
            )
        self.name = name

    def set_process(self, resources):
        self.process = self.dal.plan.get_path(self.name,
                                              self.origin.location,
                                              in_resources
                                              )


class PushRunner(ProcessRunner):
    pass

class Generator(ProcessRunner):
    def set_process(self):
        pass


class StepRunner:
    """Sync version of path"""
    def __init__(self, process):
        self.process = process
        self.method = MethodRepo.get(self.method_name)

    def execute(self, in_resources, devices, controller=None):
        if self.method:
            self.method(self.process, in_resources, devices, controller)


  #       self.location = self.dal.get_location(self.env.pars['location'])
#         self.main_process_name = self.env.pars['main_process_name']

#         self.save_after_time = self.env.pars.get('save_after_time', 0)

#         generator = self.dal.plan.get_generator_by_location(self.location)
#         self.generator_runner = OperationRunner(generator)

#         self.resource = None
#         self.main_process = None

#         self.item_queue = Queue()
#         self.stop_service = Event()
#         self.responsible = None

#     def set_responsible(self, key):
#         self.responsible = self.dal.do.get_operator(key)

#     def enter_item(self, item_data, unique=True):
#         tracking = item_data['tracking']
#         resource_key = item_data['resource_key']
#         item = self.dal.do.get_item(tracking, resource_key)

#         # If item exist out of location and unique, raise Error
#         if unique and (item is not None):
#             if self.location.key != dut.get_stocks().keys():
#                 raise InsertItemError(
#                     'Item {} is not available'.format(tracking)
#                 )

#         if item is None and self.generator_runner is not None:
#             self.generator.execute(item_data)

#         self.item_queue.put(item)

#     def setup_process(self, resource):
#         change_process = False
#         if self.main_process is None:
#             change_process = True
#         else:
#             change_process = (resource in
#                               self.main_process.get_possible_outputs())
#         if change_process:
#             self.main_process = self.dal.plan.get_process(self.main_process_name,
#                                                      resource)
#         self.resource = resource

#     def stop(self):
#         self.stop_service.set()

#     def run(self):
#         self.dal.open_session()
#         self.main_porcess
#         while True:
#             # There is a responsible and an out resource fixed
#             if self.resource and self.responsible:
#                 self.current_item = self.item_queue.get()
#                 if current_item is None:
#                     break  # Service should finish
#                 if current_item.resource != self.resource:
#                     self.setup_process(current_item.resource)
#                 try:
#                     process_runner = OperationRunner(
#                         self.main_process,
#                         self.current_item,
#                         view=self.view,
#                         stop_event=self.stop.service
#                         )
#                     process_runner.start()
#                     if self.save_after_time:
#                         Timer(self.save_after_time, self.dal.save_session)
#                     process_runner.join()
#                 except e:
#                     raise e



#                 finally:
#                     self.dal.save_session()


# class LocationQueue(Queue):
#     def __init__(self, location, max_items=1):
#         self.location = location
#         stocks = location.stocks()
#         if len(stocks) > max_items():
#             pass
#         for movement in location.stocks():
#             pass

#     def load_item(self, item_data):
#         if

class LocationQueue(Queue):
    pass


class InspectionManager:
    """Manage one tree of controls"""
    def __init__(self, environment):

        self.env = environment
        self.dal = self.env.dal
        self._partnumber = None
        self.process_inspector = None
        self.process = None
        self.batches = {}

    def set_process(self, value):
        """Load device repository for the current process"""
        self.process = value
        cavities = self.process.main_device.pars.get('cavities', 1)

        self.inspectors = [None] * cavities

        test_plan = self.dal.check.get_test_plan(self.process)
        if test_plan:
            self.process_inspector = Inspector(test_plan,
                                               responsible=self.responsible)

    def set_operator(self, value):
        self.operator = value

    def setup_batch(self, batch, cavity=None):
        """Load inspectors and their controls into the service"""
        for inspector in self.inspectors:
            inspector.session.stop()

        load_controls = self.batch is None
        if not load_controls:
            load_controls = (self.batch.partnumber == batch.partnumber)
        self.batch = batch
        if not load_controls:
            return None

        control_plans = self.dal.get_test_plan(self.process,
                                               batch.partnumber)
        self.inspectors = []
        for control_plan in control_plans:
            n_inspectors = getattr(control_plan, 'inspectors', 1)
            resolution = getattr(control_plan, 'resolution', 0)
            for _ in range(n_inspectors):
                inspector = Inspector(self)
                inspector.setup_batch(control_plan.controls, resolution)
                self.inspectors.append(inspector)

        for inspector in self.inspectors:
            inspector.session.start()

    def receive_part(self, part, cavity=0):
        if part.batch != self.batch:
            self.setup_batch(part.batch)
        self.inspectors[cavity].receive_part(part)

    def check_finished(self, inspector, check):
        if inspector.session.resolution != 0:
            self.env.session.add(check)
            self.env.session.commit()

        self.env.view.update_check(check)

    def check_initialized(self, check, cavity):
        self.env.view.update_check(inspector, check)

    def test_initalized(self, inspector, test):
        pass

    def test_finished(self, inspector, test):
        self.env.view.show_test_finished(inspector, test)
        if inspector.session.resolution == 0:
            self.env.session.add(test)


class InspectionSession(Thread):
    """Base class for inspection sessions, manages a secuence of
control_runners"""

    def __init__(self, inspector, resolution=0):
        """"Inits with inspector inspection,  resolution = 0 means
it waits till even init cycle is set"""
        super().__init__()
        self.inspector = inspector
        self.cycle_stopped = False
        self.session_stopped = False
        self.resolution = resolution

    def _process_cycle(self):
        for control_runner in self.inspector.control_runners:
            if self.cycle_stopped:  # Interrupts just before the test begins
                self.inspector.test.state = 'cancelled'
                return None
            else:
                check = control_runner.count()
                if check:
                    self.inspector.service.check_initialized(self.inspector,
                                                             check)
                    control_runner.run(check)
                    # Asyncronous method
                    wait_time = check.control.pars.get('wait_time', 1)
                    while check.state == 'ongoing':  # Asyncronous (long time) method
                        if self.cycle_stopped:
                            check.cancel()
                            check.state = 'cancelled'
                            self.inspector.test.state = 'cancelled'
                            return None
                        time.sleep(wait_time)
                    check.eval()
                    self.inspector.service.check_finished(self.inspector,
                                                          check)

    def run(self):
        while True:
            self.inspector.current_part = self.inspector.parts_queue.get()
            if self.session_stopped:
                break
            self.inspector.test = Test()
            self.inspector.service.test_initalized(self.inspector)
            self._process_cycle()
            if self.inspector.test.checks:
                self.inspector.service.test_finished(self.inspector)
            else:
                del(self.inspector.test)
            self.cycle_stopped = False
            if self.resolution != 0:
                self.inspector.parts_queue.set(None)
            time.sleep(self.resolution)

    def stop_cycle(self):
        """Stops a cycle as soon as possible"""
        self.cycle_stopped = True

    def stop(self):
        """Stop session but waits till cycle ends"""
        self.session_stopped = True
        if self.inspector.parts_queue.empty():
            self.inspector.parts_queue.put(None)
        self.join()

    def interrupt(self):
        self.stop_cycle()
        self.stop_session()


class Inspector:

    def __init__(self, service, responsible):
        super().__init__()
        self.service = service
        self.control_runners = []
        self.current_part = None
        self.parts_queue = Queue()
        self.responsible = responsible

    def setup_batch(self, controls):
        self._load_controls(controls)
        self.session = InspectionSession(self)
        self.session.start()

    def receive_part(self, part):
        self.parts_queue.set(part)

    def start_ongoing(self, controls, resolution):
        """Begins a continous session no dependent of parts"""
        self._load_controls(controls)
        self.session = InspectionSession(self, resolution)
        self.session.start()

    def _load_controls(self, controls):
        for control in controls:
            self.control_runners.append(
                ControlRunner(self, control)
                )

    def eval_value(self, value, characteristic, uncertainty,
                   modes=['low', 'high', 'suspicious']):

        limits = characteristic.limits
        repo_fry = self.service.env.repo_fry
        failure_mode_repo = repo_fry.get('FailureMode')

        mode = None

        low_limit = limits[0]
        if low_limit is not None:
            sure_low = low_limit + uncertainty
            if value < sure_low:
                mode = '{} {}'.format(modes[2], modes[0])
            if value < low_limit:
                mode = modes[0]

        top_limit = limits[1]
        if top_limit is not None:
            sure_top = top_limit - uncertainty
            if value > sure_top:
                mode = '{} {}'.format(modes[2], modes[1])
            if value > top_limit:
                mode = modes[1]

        failure_mode = None
        if mode:
            failure_mode = failure_mode_repo.get(mode, characteristic)

        return failure_mode


class ControlRunner:
    """Execute the method of the control only if satisfy sampling criteria"""
    def __init__(self, inspector, control):
        self.inspector = inspector
        self.control = control
        self.method = self.inspector.service.env.method_repo.get(
            control.method_name)

    def count(self):
        if self.control.sampling.check_is_needed():
            part = getattr(self.inspector, 'current_part', None)
            return Check(self.inspector.test, self.control, part)

    def run_method(self, check):
        self.method(self.inspector, check)
