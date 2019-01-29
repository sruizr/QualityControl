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

    def get_measurement(self, requirement, index=None, ms_chain=None):

        eid = '>{}'.format(requirement.eid) if requirement.eid else ''
        sufix = '' if index is None else '_{:02d}'.format(index)
        tracking = requirement.characteristic.key + eid + sufix
        tracking = '{}/{}'.format(self.tracking, tracking)

        # if ms_chain:
        #     tracking = '{} [{}]'.format(
        #         tracking, ', '.join([ms.tracking for ms in ms_chain])
        #     )

        for measurement in self.measurements:
            if measurement.tracking == tracking:
                return measurement

        measurement = Measurement(requirement.characteristic, tracking, self)
        if measurement not in self.measurements:
            self.measurements.append(measurement)
        return measurement

    def get_defect(self, requirement, mode_key, index=None):
        """Add defect to subject if not exist and return it
        """
        failure_mode = requirement.characteristic.failure_modes[mode_key]

        eid = '>{}'.format(requirement.eid) if requirement.eid else ''
        sufix = '' if index is None else '_{:02d}'.format(index)
        tracking = failure_mode.key + eid + sufix
        tracking = '{}/{}'.format(self.tracking, tracking)

        for defect in self.defects:
            if defect.tracking == tracking:
                return defect

        defect = Defect(failure_mode, tracking, self)
        if defect not in self.defects:
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
        super().start(**kwargs)

    def close(self):
        if self.state in ('done', 'walking'):
            if self.state == 'walking':
                self._cancel = True
            state = 'failed' if self.has_failed() else 'success'

            self.state = state
            if state == 'success':
                self.part.move(self.control_plan.source,
                               self.control_plan.destination,
                               self)
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
    @property
    def description(self):
        return self.control.requirement.description

    @property
    def test(self):
        return self.operation

    @property
    def control(self):
        return self.step

    def start(self, **inputs):
        super().start(**inputs)
        self.measurements = []
        self.defects = []
        self._remove_part_defects()

    def _remove_part_defects(self):
        location = self.source if self.source else self.test.source
        self._remove_requi_defects(self.requirement, location)

    def _remove_requi_defects(self, requi, location):
        req_key = '{}.{}'.format(requi.characteristic.key, requi.eid)
        for defect in part.defects:
            if requi_key in defect.tracking:
                defect.clear(location, self)
                for loc in location.sub_locations:
                    defect.clear(loc, self)
        for req in requi.requirements.values():
            self._remove_requi_defects(requi, location)

    def close(self):
        """Eval results once check is finished, if ttf raises DefectFound
        """
        if self.state == 'done':
            self.state = 'nok' if self.defects else 'ok'
            location = self.source if self.source else self.test.source
            location = (
                location
                if self.cavity is None else
                location.sub_locations['{}_{}'.format(location.key, self.cavity)]
            )

            for defect in self.defects:
                defect.update_qty(defect.ocurrence,
                                  location, check)

            for measurement in self.measurements:
                measurement.tokens.append(Token(
                    measurement, location, measurement.value,self
                ))

            self.finished_on = datetime.datetime.now()
            if self.state == 'nok':
                self.control.get_reaction()(self)
                if self.tff:
                    raise DefectFound()


    def add_measurement(self, requirement, value, index=None, ms_chain=None,
                        link_part=True, uncertainty=0):
        """Add measurement of a characteristic to check
        """

        subject = self.part if link_part else ms_chain[0]
        measurement = subject.get_measurement(requirement, index, ms_chain)

        self.measurements.append(measurement)
        measurement.value = value

        mode_key = measurement.eval_value(value, requirement.specs,
                                          uncertainty=uncertainty)
        if mode_key:
            self.add_defect(requirement, mode_key, index, ms_chain, link_part)

    def add_defect(self, requirement, mode_key, index=None, ms_chain=None,
                   link_part=True, ocurrence=1):
        """Add defect of check
        """
        failure_mode = requirement.characteristic.failure_modes[mode_key]
        subject = self.part if link_part else ms_chain[0]

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
        if self.reaction_name:
            return get_function(self.reaction_name)
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
