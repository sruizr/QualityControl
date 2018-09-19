# import documents as docs
#import quactrl.models.operations as ops
import datetime


class Check:
    """Verification of a characteristic on a part, outputs defects...
    """
    def __init__(self, operation, control, responsible):
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
            if key in ('part', 'machine', 'environment' ):
                key = 'subject'
            setattr(self, key, value)

        self.started_on = datetime.datetime.now()
        self.state = 'started'

    def execute(self):
        """Run control method
        """
        method = self.control.get_method()
        method(self)

        # if method inserts a thread attribute on check,
        # the execution is not finished(async)
        if hasattr(self, 'thread'):
            self.state == 'ongoing'
        else:
            self.state == 'finished'

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
            self.thread.join()
            self.state = 'cancelled'
            self.finished_on = datetime.datetime.now()

    def add_measurement(self, characteristic, value, tracking=None):
        """Add measurement of a characteristic to check
        """
        pass

    def add_defect(self, failure_mode, qty=1, tracking=None):
        """Add defect of check
        """
        pass


class Control:
    """Quality control of characteristic on a subject

    A subject can be a machine, environment or material
    """
    def __init__(self, route, part_group, characteristic, sampling='100%',
                 method=None, reaction=None):
        self.route = route
        self.sequence = route.steps[-1].sequence + 5 if route.steps else 0
        route.steps.append(self)

        self.characteristic = characteristic
        self.sampling = sampling
        self.method = method
        self.reaction = reaction
        self.counter = None

    def count(self, item):
        """Counts item (time or units)
        and using sampling decides to create check or not
        """
        pass

    def _create_check(self, operation, responsible=None):
        pass


    def get_method(self):
        """Return a method to be executable by check
        """
        pass

    def get_reaction(self):
        """Return a reaction method to be executed if check is nok
        """
        pass


class Sampling:
    pass


class Method:
    def __init__(self, m_class, comment):
        pass


class Failure:
    """Failure on part
    """
    def __init__(self, part, failure_mode):
        super().__init__(parent=part, resource=failure_mode)
        self.part.failures[failure_mode.characteristic] = self

    @property
    def failure_mode(self):
        return self.resource

    @property
    def part(self):
        return self.parent

    def add_defect_from_check(self, check, qty=1):
        return Defect


class Defect:
    """Defect on part after a check action
    """
    def __init__(self, failure, check, qty):
        super().__init__(item=failure, producer=check, qty=qty)

    @property
    def failure_mode(self):
        return self.item

    @property
    def check(self):
        return self.producer


class Measurement:
    """Measurement of characteristic on a part/process
    """
    def __init__(self, part, characteristic):
        super().__init__(parent=part, resource=characteristic)
        self.measures = []

    @property
    def characteristic(self):
        return self.resource

    @property
    def part(self):
        return self.parent

    def eval_measure_on_check(self, check, value):
        measure = Measure(self, check)
        defect = measure.eval(value)
        if defect:
            self.part.defects.append(defect)

        return defect


class Measure:
    """Result of measurement after a check action
    """
    def __init__(self, measurement, check):
        super().__init__(item=measurement, producer=check, qty=None)

    @property
    def measurement(self):
        return self.item

    @property
    def value(self):
        return self.qty

    def eval(self, value):
        self.qty = value


class InspectionReport:
    def __init__(self, reporter, samples):
        super().__init__(reporter)
        self.samples = samples
