import datetime
from quactrl.helpers import get_function
from quactrl.models.operations import Step, Action, Operation, Route


class DefectFound(Exception):
    pass


class ControlPlan(Route):
    def implement(self, responsible, update=None):
        return Test(self, responsible, update)


class Test(Operation):
    def close(self):
        if self.state in ('done', 'walking'):
            if self.state == 'walking':
                self._cancel = True
            state = 'success'
            for action in self.actions:
                if action.state == 'nok':
                    state = 'failed'
                    break
            self.state = state
            self.finished_on = datetime.datetime.now()


class Check(Action):
    """Verification of a characteristic on a part, outputs defects...
    """
    def __init__(self, operation, control, update=None):
        super().__init__(operation, control, update)
        self.measurements = []
        self.defects = []

    @property
    def control(self):
        return self.step

    def close(self):
        """Eval results once check is finished, if ttf raises DefectFound
        """
        if self.state == 'done':
            self.state = 'nok' if self.defects else 'ok'
            self.finished_on = datetime.datetime.now()
            if self.state == 'nok':
                self.control.get_reaction()(self)
                tff = self.inbox.get('tff', True)
                if tff:
                    raise DefectFound()

        # for measurement in self.measurements:
        #     self.put(measurement, self.parent.route.destination)

        # for defect in self.defects:
        #     self.put(defect, self.parent.route.destination)

    def add_measurement(self, requirement, value, index=None):
        """Add measurement of a characteristic to check
        """
        tracking = requirement.eid
        if index is not None:
            tracking = '{}_{}'.format(tracking, index)
        measurement = Measurement(self.inbox['part'],
                                  requirement.characteristic, tracking, value)
        mode_key = measurement.eval_value(requirement.specs['limits'])
        if mode_key:
            self.add_defect(requirement, mode_key, tracking, 1)

        self.measurements.append(measurement)

    def add_defect(self, requirement, mode_key, index=None, qty=1):
        """Add defect of check
        """
        failure_mode = requirement.characteristic.failure_modes[mode_key]
        tracking = requirement.eid
        if index is not None:
            tracking = '{}_{}'.format(tracking, index)
        defect = Defect(self.inbox['part'], failure_mode, tracking, qty)
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
    def __init__(self, subject, characteristic, tracking, value):
        self.subject = subject
        subject.measurements.append(self)

        self.characteristic = characteristic
        self.trackig = tracking
        self.value = value

    def eval_value(self, limits,  uncertainty=0):
        mode_key = None
        low_limit, high_limit = limits

        if high_limit is not None and self.value >= high_limit - uncertainty:
            mode_key = 'hi' if self.value > high_limit else 'shi'

        if low_limit is not None and self.value <= low_limit + uncertainty:
            mode_key = 'lo' if self.value < low_limit else 'slo'

        if low_limit > high_limit:
            mode_key = None if mode_key else 'lo'

        return mode_key


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

    def implement(self, operation):
        """Counts item (time or units)
        and using sampling decides to create check or not
        """
        if self.sampling.count(operation):
            return Check(operation, self, operation.update)

    def get_reaction(self):
        """Return a reaction method to be executed if check is nok
        """
        if self.reaction_name:
            return get_function(self.reaction_name)
        return lambda check: None


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
        self.key = "{}-{}".format(mode.key, characteristic.key)

        self.characteristic.failure_modes[mode.key] = self

    def __str__(self):
        return '{} {} @ {}'.format(self.mode.name, self.characteristic.attribute.name,
                                   self.characteristic.element.name)

class Mode:
    def __init__(self, key, name):
        self.key = key
        self.name = name
