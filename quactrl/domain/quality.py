import graph
import documents as docs
import operations as ops


class Control(ops.Step):
    """Definition of control of characteristic on a part
    """
    def __init__(self, route, characteristic, sampling='100%', method=None,
                 reaction=None):
        self.route = route
        self.characteristic = characteristic
        self.sampling = sampling
        self.method = method
        self.reaction = reaction


class Method:
    def __init__(self, m_class, comment):
        pass


class Check(ops.Action):
    """Verification of a characteristic on a part, outputs defects...
    """


    def __init__(self, operation, control):
        super().__init__(operation=operation, step=control)

    def run(self):
        pass


class Failure(graph.Item):
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


class Defect(graph.Token):
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


class Measurement(graph.Item):
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


class Measure(graph.Token):
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


class InspectionReport(docs.Report):
    def __init__(self, reporter, samples):
        super().__init__(reporter)
        self.samples = samples
