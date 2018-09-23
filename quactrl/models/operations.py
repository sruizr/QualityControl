import datetime
from quactrl.helpers import get_function


class Person:
    pass


class Device:
    """Device from a location to be used for operations
    """
    pass


class Location:
    """Site of products
    """
    pass


class PartModel:
    pass


class PartGroup:
    """Clasification of part models
    """
    pass


class Batch:
    """Result of an operation action
    """
    pass





class Part(Batch):
    """Part with unique serial number
    """
    def __init__(self, **kwargs):
        super().__init__(qty=1, **kwargs)


class IncorrectOperationState(Exception):
    pass


class Operation:
    """Add value stream action over a batch
    """
    def __init__(self, route, parent=None, responsible=None):
        self.route = route
        self.responsible = responsible

        self.parent = parent
        if parent:
            self.parent.add_action(self)
            self.responsible = parent.responsible

        self.operations = []
        self.inputs = {}
        self.outputs = {}
        self.state = 'open'
        self._cancel = False
        self.on_op = None

    def start(self, **inputs):
        self.inputs.update(inputs)
        self.started_on = datetime.datetime.now()
        self.state = 'started'
        self.current_action = None

    def execute(self):
        """Execute method asociated to route
        """
        method = self.route.get_method()
        method(self, **self.route.method_pars)
        if hasattr(self, 'thread'):
            self.state = 'ongoing'
        else:
            self.state = 'finished'

    def walk(self):
        """Execute each child operation
        """
        self.state = 'walking'
        for op in self._list_subops():
            if op:  # step could no create operation!
                self.on_op = op
                op.start(**self.inputs)
                op.execute()
                if op.state == 'ongoing':
                    op.thread.join()
                op.close()
                self.on_op = None
        self.state = 'walked'

    def _list_subops(self):
        for step in self.route.steps:
            if self._cancel:
                break
            else:
                yield step.create_operation(self)

    def close(self):
        if self.state == 'finished':
            self.state = 'closed'
            self.finished_on = datetime.datetime.now()

    def cancel(self):
        """Cancel execution of operation
        """
        if self.state == 'ongoing':
            self.thread.cancel()
        elif self.state == 'walking':
            self._cancel = True
            self.current_op.cancel()
        self.state = 'cancelled'
        self.finished_on = datetime.datetime.now()

class Route:
    """Planning of an operation on parts
    """
    def __init__(self, inputs, outputs, source, destination):
        self.steps = []
    def __init__(self, route, part_group, characteristic, sampling='100%',
                 method=None, method_pars=None, reaction=None):
        self.route = route
        self.sequence = route.steps[-1].sequence + 1 if route.steps else 0
        route.steps.append(self)

        self.characteristic = characteristic
        self.last_count = 0
        self.sampling = Sampling(self, *self._sampling_par[sampling])
        self.method_name = method
        self.method_pars = method_pars if method_pars else {}
        self.reaction_name = reaction

    def create_action(self, operation):
        """Counts item (time or units)
        and using sampling decides to create check or not
        """
        if self.sampling.count(operation):
            return Check(operation, self)

    def get_method(self):
        """Return a method to be executable by check
        """
        return get_function(self.method_name)
