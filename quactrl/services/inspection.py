import threading


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
        controls = self.env.session.ControlRepository(self.process, batch)
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
    """Run a complete sequence of controls within a thread"""
    def __init__(self, service):
        super().__init__()
        self.env = service.env
        self.service = service
        self.part_arrives = Event()
        self.part_arrives.clear()

    def run(self):
        """Run the full sequence of checks every time a part arrives or """
        while not self.stop_signal.is_set:
            self.part_arrives.wait()
            test = Test()
            for control_runner in self.control_runners:


    def eval_value(self, value, characteristic, uncertainty, modes=['low', 'high', 'suspcious']):

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

    def execute_method(self, check):
        self.service.starting(check)

        self.env.session.add(check)
        method = self.env.method_repo.get(check.control.method_name)
        method_pars = check.control.pars
        check.state = 'Ongoing'
        method(self, check)
        is_async = method_pars.get('is_async', False)
        if is_async:
            refresh_time = method_pars.get('refresh_time', 5)
            while check.state == 'Ongoing':
                time.sleep(refresh_time)

        if check.failures:
            self.service.check_has_failled(check)
        else:
            self.service.finished(check)

class ControlRunner:
    pass


class SampleController:
    pass
