import datetime
from quactrl.helpers import get_function
from quactrl.models.core import Item, Resource, UnitaryItem, Token
import quactrl.models.operations as op


class DefectFound(Exception):
    pass


class Subject(UnitaryItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.measurements = []
        self.defects = []

    def get_measurement(self, requirement, index=None):
        """Return measurement instance of subject
        """
        eid = '>{}'.format(requirement.eid) if requirement.eid else ''
        sufix = '' if index is None else '_{:02d}'.format(index)
        tracking = requirement.characteristic.key + eid + sufix
        tracking = '{}/{}'.format(self.tracking, tracking)

        for measurement in self.measurements:
            if measurement.tracking == tracking:
                return measurement

        # No found, creating a new one
        measurement = Measurement(requirement.characteristic, tracking, self)
        if measurement not in self.measurements:
            self.measurements.append(measurement)
        return measurement

    def get_defect(self, requirement, mode_key, index=None):
        """Return defect instance of subject
        """
        failure_mode = requirement.characteristic.failure_modes[mode_key]

        eid = '>{}'.format(requirement.eid) if requirement.eid else ''
        sufix = '' if index is None else '_{:02d}'.format(index)
        tracking = failure_mode.key + eid + sufix
        tracking = '{}/{}'.format(self.tracking, tracking)

        for defect in self.defects:
            if defect.tracking == tracking:
                return defect

        # Not found, creating a new one
        defect = Defect(failure_mode, tracking, self)
        if defect not in self.defects:
            self.defects.append(defect)
        return defect

    def clear_defects(self, check):
        self._clear_requi_defects(check.control.requirement, check)

    def _clear_requi_defects(self, requi, check):
        req_key = '{}>{}'.format(requi.characteristic.key, requi.eid)
        for defect in self.defects:
            if req_key in defect.tracking:
                defect.clear(check.location, check)
                for loc in check.location.sub_locations:
                    defect.clear(loc, check)

        for req in requi.requirements.values():
            self._clear_requi_defects(req, check)


class ControlPlan(op.Route):
    def implement(self, responsible, update=None):
        return self.can_implement(Test, responsible, update)


class Test(op.Operation):
    def start(self, **kwargs):
        super().start(**kwargs)
        self.part.update_qty(1, self.control_plan.source, self)

    def close(self):
        if self.status in ('done', 'walking'):
            if self.status == 'walking':
                self._cancel = True
            status = 'failed' if self.has_failed() else 'success'

            self.status = status
            if status == 'success':
                self.part.move(self.control_plan.source,
                               self.control_plan.destination,
                               self)
            self.finished_on = datetime.datetime.now()

    def has_failed(self):
        """Even is not finished returns if test is nok
        """
        for action in self.actions:
            if action.status in ('nok', 'cancelled'):
                return True
        return False


class Check(op.Action):
    """Verification of a characteristic on a part, outputs defects...
    """
    @property
    def description(self):
        return self.control.requirement.description

    @property
    def test(self):
        return self.operation

    @property
    def control(self):
        return self.step

    @property
    def location(self):
        if not hasattr(self, '_location'):
            self._location = (self.control.source if self.control.source
                              else self.test.control_plan.source)
        return self._location

    def start(self, **inputs):
        super().start(**inputs)
        self.measurements = []
        self.defects = []
        self.part.clear_defects(self)
        for device in self.devices.values():
            device.clear_defects(self)

    def close(self):
        """Eval results once check is finished, if ttf raises DefectFound
        """
        if self.status == 'done':
            self.status = 'nok' if self.defects else 'ok'

            location = (
                self.location
                if self.cavity is None else
                 self.location.sub_locations['{}_{}'.format(self.location.key, self.cavity)]
            )

            for defect in self.defects:
                defect.update_qty(defect.ocurrence,
                                  location, self)

            for measurement in self.measurements:
                measurement.tokens.append(Token(
                    measurement, location, measurement.value, self
                ))

            self.finished_on = datetime.datetime.now()
            if self.status == 'nok':
                self.control.get_reaction()(self)
                if self.tff:
                    raise DefectFound()


    def add_measurement(self, requirement, value, subject=None, index=None, uncertainty=0):
        """Add measurement of a characteristic to check
        """
        if not subject:
            subject = self.part
        measurement = subject.get_measurement(requirement, index)

        self.measurements.append(measurement)
        mode_key = measurement.eval_value(value, requirement.specs,
                                          uncertainty=uncertainty)

        if mode_key:
            self.add_defect(requirement, mode_key, subject, index)

    def add_defect(self, requirement, mode_key, subject=None, index=None, ocurrence=1):
        """Add defect of check
        """
        if not subject:
            subject = self.part

        failure_mode = requirement.characteristic.failure_modes[mode_key]

        defect = subject.get_defect(requirement, mode_key, index)
        defect.ocurrence = ocurrence

        self.defects.append(defect)


class Defect(Item):
    """Defect on a subject found by a check action
    """
    def __init__(self, failure_mode, tracking, subject):
        self.failure_mode = failure_mode
        self.tracking = tracking
        self.subject = subject
        self.ocurrence = None


class Measurement(Item):
    """Measurement of a subject done by a check action
    """
    def __init__(self, characteristic, tracking, subject):
        self.subject = subject
        self.characteristic = characteristic
        self.tracking = tracking
        self.value = None

    def eval_value(self, value, specs, uncertainty=0):
        self.value = value

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
        self.reaction_name = reaction

    def implement(self, operation):
        """Counts item (time or units)
        and using sampling decides to create check or not
        """
        if not hasattr(self, 'sampling'):
            self.sampling = Sampling(self, *self._sampling_par['100%'])

        if self.sampling.count(operation):
            return Check(operation, self, operation.update)

    def get_reaction(self):
        """Return a reaction method to be executed if check is nok
        """
        reaction_name = self.method_pars.get('reaction_name')
        if reaction_name:
            return get_function(reaction_name)

        return lambda check: None


class Sampling:
    def __init__(self, control,  quantity, frequency):
        self.control = control
        control.last_count = 0
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
    def __init__(self, key, name=None):
        self.key = key
        self.name = name if name else key
