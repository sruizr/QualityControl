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
        self.inbox = {}
        self.outbox = {}
        self.state = 'open'
        self._cancel = False
        self.on_op = None

    def start(self, **inputs):
        self.inbox.update(inputs)
        self.started_on = datetime.datetime.now()
        self.state = 'started'
        self.current_action = None

    def execute(self):
        """Execute method asociated to route
        """
        if (self.state == 'started'
            or self.state == 'walked'):
            method = self.route.get_method()
            if method:
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
                op.start(**self.inbox)
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


class WrongInboxContent(Exception):
    pass


class Route:
    """Planning of an operation over resources
    """
    def __init__(self, role, consumes=None, productions=None, parent=None,
                 method=None, method_pars=None):
        """Create route from planned inputs and outputs, can be embebed
        """
        self.parent = parent
        self.sequence = 0
        if parent:
            self.sequence = (parent.steps[-1].sequence + 5
                             if parent.steps else 0)
            parent.steps.append(self)

        self.consumes = consumes if consumes else []
        self.productions = productions if productions else []
        self.method_name = method
        self.method_pars = method_pars if method_pars else {}

    def create_operation(self, parent=None, responsible=None):
        """Returns operation instance from parent or responsible
        """
        return Operation(self, parent, responsible)

    def get_method(self):
        """Return a method to be executable by check
        """
        return get_function(self.method_name)

    def validate_inbox(self, inbox):
        pass
