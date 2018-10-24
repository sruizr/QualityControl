import datetime
from quactrl.helpers import get_function
from quactrl.models.operations import Operation, Step


class Check(Operation):
    """Verification of a characteristic on a part, outputs defects...
    """
    def __init__(self, operation, control):
        super().__init__(control, operation)
        self.measurements = []
        self.defects = []

    @property
    def operation(self):
        return self.parent

    @property
    def control(self):
        return self.route

    def close(self):
        """Eval results once check is finished
        """
        if self.state == 'finished':
            self.state = 'nok' if self.defects else 'ok'
            self.finished_on = datetime.datetime.now()
            if self.state == 'nok':
                self.control.get_reaction()(self)

        for measurement in self.measurements:
            self.put(measurement, self.parent.destination)

        for defect in self.defects:
            self.put(defect, self.parent.destination)

    def add_measurement(self, requirement, value, index=None):
        """Add measurement of a characteristic to check
        """
        tracking = requirement.eid
        if index is not None:
            tracking = '{}_{}'.format(tracking, index)
        measurement = Measurement(self.subject, requirement, value, tracking)
        failure_mode = measurement.eval()
        if failure_mode:
            self.add_defect(failure_mode, tracking, 1)

        self.measurements.append(measurement)

    def add_defect(self, requirement, mode_key, index=None, qty=1):
        """Add defect of check
        """
        failure_mode = requirement.characteristic.failure_modes[mode_key]
        tracking = requirement.eid
        if index is not None:
            tracking = '{}_{}'.format(tracking, index)
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
    def __init__(self, subject, requirement, tracking):
        self.subject = subject
        subject.measurements.append(self)

        self.characteristic = requirement.characteristic
        self.limits = requirement
        self.trackig = tracking
        self.value = None

    def eval_value(self, value, uncertainty=0):
        mode_key = None
        low_limit, high_limit = self.requirementcharacteristic.limits

        if high_limit is not None and value >= high_limit - uncertainty:
            mode_key = 'hi' if value > high_limit else 'shi'

        if low_limit is not None and value <= low_limit + uncertainty:
            mode_key = 'lo' if value < low_limit else 'slo'

        if mode_key:
            return self.characteristic.get_failure(mode_key)


class Control(Step):
    """Plan for checking a characteristic on a subject

    A subject can be a machine, environment or material
    """
    _sampling_par = {'100%': (1, 1)}

    def __init__(self, route, requirement, method_name, method_pars=None,
                 sampling='100%', reaction=None):

        super().__init__(route, method_name, method_pars)
        self.requirement = requirement

        self.last_count = 0
        self.sampling = Sampling(self, *self._sampling_par[sampling])
        self.reaction_name = reaction

    @property
    def characteristic(self):
        return self.outputs['characteristic']

    def create_operation(self, parent):
        """Counts item (time or units)
        and using sampling decides to create check or not
        """
        if self.sampling.count(parent):
            return Check(parent, self)

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
        self.control.last_count += self.quantity
        return True


class FailureMode:
    def __init__(self, characteristic, mode):
        self.characteristic = characteristic
        self.mode = mode

        self.characteristic.failure_modes[mode.key] = self


class Mode:
    def __init__(self, key, name):
        self.key = key
        self.name = name
