import datetime
from quactrl.helpers import get_function


class Check:
    """Verification of a characteristic on a part, outputs defects...
    """
    def __init__(self, operation, control, responsible=None):
        self.operation = operation
        operation.actions.append(self)

        if responsible is None:
            self.responsible = operation.responsible

        self.control = control
        self.subject = None  # Object to be checked
        self.measurements = []
        self.defects = []
        self.state = 'open'

    def prepare(self, **resources):
        """Load resources to be used on checking process as attributes
        """
        for key, value in resources.items():
            if key in ('part', 'machine', 'environment'):
                key = 'subject'
            setattr(self, key, value)

        self.started_on = datetime.datetime.now()
        self.state = 'started'

    def execute(self):
        """Run control method
        """
        if self.state == 'started':
            method = self.control.get_method()
            method(self, **self.control.method_pars)

            # if method inserts a thread attribute on check,
            # the execution is not finished(async)
            if hasattr(self, 'thread'):
                self.state = 'ongoing'
            else:
                self.state = 'finished'

    def close(self):
        """Eval results once check is finished
        """
        if self.state == 'finished':
            self.state = 'nok' if self.defects else 'ok'
            self.finished_on = datetime.datetime.now()
            if self.state == 'nok':
                self.control.get_reaction()(self)

    def cancel(self):
        """Cancel execution of check (only if it's asyncronous)
        """
        if self.state == 'ongoing':
            self.thread.cancel()
            self.state = 'cancelled'
            self.finished_on = datetime.datetime.now()

    def add_measurement(self, characteristic, value, tracking):
        """Add measurement of a characteristic to check
        """
        measurement = Measurement(self.subject, characteristic, value,
                                  tracking)
        failure_mode = measurement.eval()
        if failure_mode:
            self.add_defect(failure_mode, tracking, 1)

        self.measurements.append(measurement)

    def add_defect(self, failure_mode, tracking, qty=1):
        """Add defect of check
        """
        defect = Defect(self.subject, failure_mode, tracking, qty)
        self.defects.append(defect)


class Defect:
    """Defect on a subject found by a check action
    """
    def __init__(self, subject, failure_mode, tracking, qty=1):
        self.subject = subject
        subject.defects.append(self)

        self.failure_mode = failure_mode
        self.tracking = tracking
        self.qty = qty


class Measurement:
    """Measurement of a subject done by a check action
    """
    def __init__(self, subject, characteristic, tracking):
        self.subject = subject
        subject.measurements.append(self)

        self.characteristic = characteristic
        self.trackig = tracking
        self.value = None

    def eval_value(self, value, uncertainty=0):
        mode_key = None
        low_limit, high_limit = self.characteristic.limits

        if high_limit is not None and value >= high_limit - uncertainty:
            mode_key = 'hi' if value > high_limit else 'shi'

        if low_limit is not None and value <= low_limit + uncertainty:
            mode_key = 'lo' if value < low_limit else 'slo'

        if mode_key:
            return self.characteristic.get_failure(mode_key)


class Control:
    """Plan for checking a characteristic on a subject

    A subject can be a machine, environment or material
    """
    _sampling_par = {'100%': (1, 1)}

    def __init__(self, route, part_group, characteristic, sampling='100%',
                 method=None, method_pars=None, reaction=None):
        self.route = route
        self.sequence = route.steps[-1].sequence + 5 if route.steps else 0
        route.steps.append(self)

        self.characteristic = characteristic
        self.last_count = 0
        self.sampling = Sampling(self, *self._sampling_par[sampling])
        self.method_name = method
        self.method_pars = method_pars if method_pars else {}
        self.reaction_name = reaction

    def create_check(self, operation):
        """Counts item (time or units)
        and using sampling decides to create check or not
        """
        if self.sampling.count(operation):
            return Check(operation, self)

    def get_method(self):
        """Return a method to be executable by check
        """
        return get_function(self.method_name)

    def get_reaction(self):
        """Return a reaction method to be executed if check is nok
        """
        return get_function(self.reaction_name)


class Sampling:
    def __init__(self, control,  quantity, frequency):
        self.control = control
        self.quantity = quantity
        self.frequency = frequency

    def count(self, operation):
        self.control.last_count += operation.part.qty
        return True


class FailureMode:
    def __init__(self, characteristic, mode):
        self.characteristic = characteristic
        self.mode = mode

        self.characteristic.failure_modes[mode] = self
