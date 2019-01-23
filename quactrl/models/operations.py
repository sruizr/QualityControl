import datetime
import threading
from collections import namedtuple
from quactrl.helpers import get_function
from .core import Node, Resource, UnitaryItem, Path, Flow, Token


class Location(Node):
    """Site of products
    """
    def __init__(self, key, name, description=None):
        self.key = key
        self.name = name
        self.description = description


class Part(UnitaryItem):
    """Part with unique serial number
    """
    def __init__(self, model, serial_number, location=None, pars=None):
        self.model = model
        self.serial_number = serial_number
        self.pars = pars if pars else {}
        self.defects = []
        self.measurements = []

        self.add(location)
        self.dut = None

    def set_dut(self, connection):
        self.dut = self.model.create_dut(connection)

    @property
    def location(self):
        locations = [location
                     for location in self.stocks.keys()]
        return locations[0] if len(locations) == 1 else locations


class Action(Flow):
    """Implementation of a step from a route
    """
    def __init__(self, operation, step, update=None):
        super(Flow, self).__init__(operation.responsible, update)
        self.operation = operation
        self.step = step
        self.inbox = {}

    @property
    def description(self):
        return self.step.method_name

    def start(self, **inputs):
        super().start()
        self.cavity = inputs.pop('cavity')
        self.inbox.update(inputs)

    def execute(self):
        """Execute method asociated to route
        """
        if (self.state == 'started'):
            if self.step.method:
                self.step.method(self, **self.step.method_pars)
                if hasattr(self, 'thread'):
                    self.state = 'ongoing'
                else:
                    self.state = 'done'

    def cancel(self):
        """Cancel execution of operation
        """
        if self.state == 'ongoing':
            self.thread.cancel()
        self.state = 'cancelled'
        self.finished_on = datetime.datetime.now()


class Operation(Flow):
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
        self.cavity = inputs.pop('cavity')
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
            self.state = 'done'

    def walk(self):
        """Execute each child action
        """
        self.state = 'walking'
        self.on_action = None
        for action in self.action_iterator():
            if action:  # step could no create operation!
                self.on_action = action
                self.actions.append(action)
                action.start(cavity=self.cavity, **self.inbox)
                action.execute()
                if action.state == 'ongoing':
                    action.thread.join()
                    if hasattr(action, 'exception'):
                        # The thread has raised an exception
                        raise action.exception
                    action.state = 'done'
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

    def ask(self, key, **kwargs):
        self.question = Question(update=self.update)
        self.question.ask(key, **kwargs)

    def answer(self, **kwargs):
        self.question.answer(**kwargs)


class WrongInboxContent(Exception):
    pass


class Route(Path):
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


class Step(Path):
    """Planning of a sub action for a Route
    """
    def __init__(self, route, method_name, method_pars):
        self.route = route
        self.sequence = 0 if not route.steps else route.steps[-1].sequence + 5
        self.method_name = method_name
        self.method = get_function(method_name) if method_name else None
        self.method_pars = method_pars if method_pars else {}

    def implement(self, operation):
        return Action(operation, self, operation.update)


class Question(threading.Event):
    def __init__(self, update=None):
        self.update = update
        super().__init__()
        self.request = {}
        self.response = {}

    def ask(self, key, **kwargs):
        """Wait until answer is done by other thread
        """
        self.request['key'] = key
        self.request.update(kwargs)
        if self.update:
            self.update('asked', self)

        self.wait()

    def answer(self, **kwargs):
        self.response = kwargs
        if self.update:
            self.update('answered', self)
        self.set()
