import time
import threading
from asyncio.queues import Queue
from quactrl.entities import Test, Check


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

    def _run(self):
        pass


class Inspector(threading.Thread):

    def __init__(self, service, period):
        super().__init__()
        self.service = service
        self.stop_inspection = False
        self.control_runners = []
        self.period = period

    def load_controls(self, controls):
        for control in controls:
            self.control_runners.append(
                ControlRunner(control)
                )

    def eval_value(self, value, characteristic, uncertainty,
                   modes=['low', 'high', 'suspcious']):

        limits = characteristic.limits
        repo_fry = self.env.repo_fry
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

    def run(self):
        pass


class PartInspector(Inspector):
    """Inspector of parts"""
    def __init__(self, service, period):
        super().__init_(service, period)
        self._parts = Queue()
        self.current_part = None

    def run(self):
        while not self.stop_inspection:
            self.current_part = self._parts.get()
            self.test = Test()
            for control_runner in self.control_runners:
                if not self.stop_inspection:
                    check = control_runner.count()
                    if check:
                        self.service.check_initialized(self, check)
                        control_runner.run(check)
                        while check.state == 'ongoing' and not self.stop:
                            time.sleep(self.period)
                        self.service.check_finished(self, check)
            self.service.return_part(self, self.current_part)

    def receive(self, part):
        self._parts.put(part)


class ProcessInspector(Inspector):
    """Inspector of process characteristics, continuous inspection"""
    def __init__(self, service, period):
        super().__init__(service, period)

    def run(self):
        self.test = Test()
        while not self.stop_inspection:
            for control_runner in self.control_runners:
                if not self.stop_inspection:
                    check = control_runner.count()
                    if check:
                        self.service.check_initialized(self, check)
                        control_runner.run(check)
                        self.service.check_finished(self, check)
            time.sleep(self.period)


class ControlRunner:
    """Execute the method of the control only if satisfy sampling criteria"""
    def __init__(self, inspector, control):
        self.inspector = inspector
        self.control = control
        self.method = self.inspector.service.env.method_repo.get(
            control.method)

    def count(self):
        if self.control.sampling.check_is_needed():
            part = getattr(self.inspector, 'current_part', None)
            return Check(self.inspector.test, self.control, part)

    def run(self, check):
        self.method(self.inspector, check)
