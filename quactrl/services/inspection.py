import time
import threading
from queue import Queue
from quactrl.entities.check import Test, Check


class InspectionManager:
    """Manage one tree of controls"""
    def __init__(self, environment):
        self.env = environment

    def setup_session(self, process):
        """Load device repository for the current process"""
        self.process = process
        self.device_repo = self.env.session.DeviceRepository(process)

    def setup_batch(self, batch):
        """Load inspectors and their controls into the service"""
        self.batch = batch
        self.controls = self.env.session.ControlRepository(self.process, batch)
        self.inspectors = []

    def _load_control_struct(self, controls):
        control_plan = {}
        for control in controls:
            key = control.prev
            if key in control_plan.keys():
                control_plan[key].add(control)
            else:
                control_plan[key] = {control}

class InspectionSession(threading.Thread):
    """Base class for inspection sessions, manages a secuence of control_runners"""
    def __init__(self, inspector, resolution=0):
        """"Inits with inspector inspection,  resolution = 0 means it waits till even init cycle is set"""
        super().__init__()
        self.inspector = inspector
        self.cycle_stopped = False
        self.session_stopped = False
        self.resolution = resolution

    def _process_cycle(self):
        for control_runner in self.inspector.control_runners:
            if self.cycle_stopped: # Interrupts just before the check begins
                self.inspector.test.state = 'cancelled'
                return None
            else:
                check = control_runner.count()
                if check:
                    self.inspector.service.check_initialized(self, check)
                    control_runner.run(check)
                    # Asyncronous method
                    wait_time = check.control.pars.get('wait_time', 1)
                    while check.state == 'ongoing': # Asyncronous (long time) method
                        if self.cycle_stopped:
                            check.cancel()
                            check.state = 'cancelled'
                            self.inspector.test.state = 'cancelled'
                            return None
                        time.sleep(wait_time)
                    check.eval()
                    self.inspector.service.check_finished(self, check)

    def run(self):
        while True:
            self.inspector.current_part = self.inspector.parts_queue.get()
            if self.session_stopped:
                break
            self._process_cycle()
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

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.control_runners = []
        self.current_part = None
        self.parts_queue = Queue()

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
                   modes=['low', 'high', 'suspcious']):

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
