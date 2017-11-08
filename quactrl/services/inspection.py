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
        super().__init_(self)
        self.env = service.env

    def run(self):
        pass


class ControlRunner:
    pass


class SampleController:
    pass
