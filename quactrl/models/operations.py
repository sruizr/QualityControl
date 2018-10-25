import datetime
from collections import namedtuple
from quactrl.helpers import get_function


class Location:
    """Site of products
    """
    def __init__(self, key, name, description=None):
        self.key = key
        self.name = name
        self.description = description


Motion = namedtuple('Motion', 'type item location qty')


class Handling:
    def __init__(self, responsible, update=None):
        self.responsible = responsible
        self.motions = []
        self.started_on = None
        self.finished_on = None
        self.update = None
        self._state = 'open'

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state
        if self.update:
            self.update(state, self)

    def start(self):
        self.state = 'started'
        self.started_on = datetime.datetime.now()

    def get(self, item, from_location=None, qty=1):
        if not self.started_on:
            self.start()

        if from_location is not None and from_location != item.location:
            raise Exception()

        self.motions.append(Motion('GET', item, item.location, qty))
        item.location = None

    def put(self, item, to_location, qty=1):
        self.motions.append(Motion('PUT', item, item.location, qty))
        item.location = to_location
        if item.qty != qty:
            raise Exception()

    def close(self):
        self.state = 'closed'
        self.finished_on = datetime.datetime.now()


class Part:
    """Part with unique serial number
    """
    def __init__(self, model, tracking, location=None, pars=None):
        self.model = model
        self.tracking = tracking
        self.location = location
        self.defects = []
        self.measurements = []
        self.pars = pars if pars else {}
        self.dut = None

    def set_dut(self, connection):
        self.dut = self.model.device_class(connection, self.pars)


class IncorrectOperationState(Exception):
    pass


class Action(Handling):
    """Implementation of a step from a route
    """
    def __init__(self, operation, step, update=None):
        super().__init__(operation.responsible, update)
        self.operation = operation
        self.step = step

    def execute(self):
        """Execute method asociated to route
        """
        if (self.state == 'started'):
            if self.step.method:
                self.step.method(self, **self.step.method_pars)
                if hasattr(self, 'thread'):
                    self.state = 'ongoing'
                else:
                    self.state = 'finished'

    def cancel(self):
        """Cancel execution of operation
        """
        if self.state == 'ongoing':
            self.thread.cancel()
        self.state = 'cancelled'
        self.finished_on = datetime.datetime.now()


class Operation(Handling):
    """Add value stream action over a batch
    """
    def __init__(self, route, responsible, update=None):
        super().__init__(responsible, update)
        self.route = route

        self.actions = []
        self.inbox = {}
        self.outbox = {}
        self._cancel = False
        self.on_action = None

    def start(self, **inputs):
        super().start()
        self.update = inputs.paction('update', None)
        self.cavity = inputs.paction('cavity')
        self.inbox.update(inputs)

    def execute(self):
        """Execute method asociated to route
        """
        if (self.state == 'started'
                or self.state == 'walked'):
            if self.route.method:
                self.route.method(self, **self.route.method_pars)
                if hasattr(self, 'thread'):
                    self.state = 'ongoing'
                else:
                    self.state = 'done'

    def walk(self):
        """Execute each child action
        """
        self.state = 'walking'
        self.on_action = None
        for action in self.action_iterator():
            if action:  # step could no create operation!
                self.on_action = action
                action.start(cavity=self.cavity, **self.inbox)
                action.execute()
                if action.state == 'ongoing':
                    action.thread.join()
                action.close()
            self.on_action = None

        self.state = 'walked'

    def action_iterator(self):
        for step in self.route.steps:
            if self._cancel:
                break
            else:
                yield step.implement(self)

    def cancel(self):
        """Cancel execution of operation
        """
        if self.state == 'ongoing':
            self.thread.cancel()
        elif self.state == 'walking':
            self._cancel = True
        if self.on_action:
            self.on_action.cancel()
        self.state = 'cancelled'
        self.finished_on = datetime.datetime.now()


class WrongInboxContent(Exception):
    pass


class Route:
    """Planning of an operation over resources
    """
    def __init__(self, role, source=None, destination=None,
                 outputs=None, parent=None,
                 method_name=None, method_pars=None):
        """Create route from planned inputs and outputs, can be embebed
        """
        self.parent = parent
        self.sequence = 0
        self.source = source
        self.destination = destination
        self.steps = []

        self.outputs = outputs if outputs else []
        self.method = get_function(method_name) if method_name else None
        self.method_pars = method_pars if method_pars else {}

    def implement(self, responsible, update=None):
        """Returns operation instance from parent or responsible
        """
        return Operation(self, responsible, update)

    def validate_inbox(self, inbox):
        pass


class Step:
    """Planning of a sub action for a Route
    """
    def __init__(self, route, method_name, method_pars):
        self.route = route
        self.sequence = 0 if not route.steps else route.steps[-1].sequence + 5
        self.method = get_function(method_name) if method_name else None
        self.method_pars = method_pars if method_pars else {}

    def implement(self, operation):
        return Action(operation, self, operation.update)
