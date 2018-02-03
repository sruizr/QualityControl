import time
from threading import Thread, Event, Timer
from queue import Queue
from quactrl.domain.check import Test, Check
from quactrl.domain import get_component
import pdb




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
