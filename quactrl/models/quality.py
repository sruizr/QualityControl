import datetime
from quactrl.helpers import get_function
from quactrl.models.core import Item, Resource
import quactrl.models.operations as op


class DefectFound(Exception):
    pass


class Subject(Item):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.measurements = []
        self.defects = []

    def add_measurement(self, characteristic, tracking, value):
        for measurement in self.measurements:
            if measurement.tracking == tracking:
                measurement.flow_qty = value
                return measurement

        measurement = Measurement(characteristic, tracking, value, self)
        self.measurements.append(measurement)
        return measurement

    def add_defect(self, failure_mode, tracking, qty=1):
        """Add defect to subject if not exist and return it
        """
        for defect in self.defects:
            if defect.tracking == tracking:
                defect.qty = qty
                return defect

        defect = Defect(failure_mode, tracking, self, qty)
        self.defects.append(defect)
        return defect

    def clear_defects(self, check):
        self._clear_defects_by_requi(check.control.requirement, check)

    def _clear_defects_by_requi(self, requirement, check):
        for defect in self.defects:
            if requirement.eid in defect.tracking:
                defect.clear(check)
            for requi in requirement.requirements.values():
                self._clear_defects_by_requi(requi, check)


class ControlPlan(op.Route):
    def implement(self, responsible, update=None):
        return Test(self, responsible, update)


class Test(op.Operation):
    def start(self, **kwargs):
        if 'part' in kwargs:
            self.part = kwargs['part']
        super().start(**kwargs)

    def close(self):
        if self.state in ('done', 'walking'):
            if self.state == 'walking':
                self._cancel = True
            state = 'failed' if self.has_failed() else 'success'

            self.state = state
            self.finished_on = datetime.datetime.now()

    def has_failed(self):
        """Even is not finished returns if test is nok
        """
        for action in self.actions:
            if action.state in ('nok', 'cancelled'):
                return True
        return False


class Check(op.Action):
    """Verification of a characteristic on a part, outputs defects...
    """
    def __init__(self, operation, control, update=None):
        super().__init__(operation, control, update)
        self.measurements = []
        self.defects = []

    @property
    def description(self):
        return self.control.requirement.description

    @property
    def test(self):
        return self.operation

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

    def _get_tracking(self, requirement, index, ms_chain):
        prefix = ms_chain.join('*') + '-' if ms_chain else ''
        sufix = '_{}'.format(index) if index else ''
        return prefix + requirement.eid + sufix

    def add_measurement(self, requirement, value, index=None, ms_chain=None,
                        link_part=True, uncertainty=0):
        """Add measurement of a characteristic to check
        """
        tracking = self._get_tracking(requirement, index, ms_chain)
        subject = self.inbox['part'] if link_part else ms_chain[0]
        measurement = subject.add_measurement(requirement.characteristic,
                                              tracking, value)
        self.measurements.append(measurement)

        mode_key = measurement.eval_value(requirement.specs,
                                          uncertainty=uncertainty)
        if mode_key:
            self.add_defect(requirement, mode_key, index, ms_chain, link_part)

    def add_defect(self, requirement, mode_key, index=None, ms_chain=None,
                   link_part=True, qty=1):
        """Add defect of check
        """
        failure_mode = requirement.characteristic.failure_modes[mode_key]
        subject = self.inbox['part'] if link_part else ms_chain[0]
        tracking = self._get_tracking(requirement, index, ms_chain)
        defect = subject.add_defect(failure_mode, tracking, qty)
        self.defects.append(defect)


class Defect(Item):
    """Defect on a subject found by a check action
    """
    def __init__(self, failure_mode, tracking, subject, qty=1):
        self.failure_mode = failure_mode
        self.tracking = tracking
        self.subject = subject
        self.qty = qty


class Measurement(Item):
    """Measurement of a subject done by a check action
    """
    def __init__(self, characteristic, tracking, value, subject):
        self.characteristic = characteristic
        self.tracking = tracking
        self.value = value

        subject.measurements.append(self)
        self.subject = subject

    def eval_value(self, specs, uncertainty=0):
        low_limit = high_limit = None
        if 'limits' in specs:
            low_limit, high_limit = specs['limits']
            value = self.value
        elif 'max_abs' in specs:
            high_limit = specs['max_abs']
            value = abs(self.value)

        mode_key = None
        if high_limit is not None and value > high_limit - uncertainty:
            mode_key = 'hi' if value > high_limit else 'shi'

        if low_limit is not None and value < low_limit + uncertainty:
            mode_key = 'lo' if value < low_limit else 'slo'

        if not (low_limit is None or high_limit is None):
            if low_limit > high_limit:
                mode_key = None if mode_key else 'lo'

        if mode_key and 'max_abs' in specs:
            mode_key = list(self.characteristic.failure_modes.keys())[0]

        return mode_key


class Control(op.Step):
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


class FailureMode(Resource):
    """Mode of failing a characteristic
    """
    def __init__(self, characteristic, mode):
        self.characteristic = characteristic
        self.mode = mode
        self.key = "{}-{}".format(mode.key, characteristic.key)

        self.characteristic.failure_modes[mode.key] = self

    def __str__(self):
        return '{} {} @ {}'.format(self.mode.name,
                                   self.characteristic.attribute.name,
                                   self.characteristic.element.name)

    @property
    def description(self):
        return str(self)


class Mode(Resource):
    """Modes clasification of failing a characteristic
    """
    def __init__(self, key, name):
        self.key = key
        self.name = name
