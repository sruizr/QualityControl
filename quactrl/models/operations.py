import datetime
import threading
from quactrl.helpers import get_function
from .core import Node, Resource, UnitaryItem, Path, Flow, Token


class NotAuthorizedException(Exception):
    pass


class Location(Node):
    """Site of products
    """
    def __init__(self, key, name=None, description=None):
        self.key = key
        self.name = name if name else key
        self.description = description
        self.sub_locations = {}


class Action(Flow):
    """Implementation of a step from a route
    """
    def __init__(self, operation, step, update=None):
        super().__init__(operation.responsible, update)
        self.operation = operation
        self.step = step

    @property
    def description(self):
        return self.step.method_name

    def start(self, **inputs):
        super().start()
        for attr, value in inputs.items():
            setattr(self, attr, value)

    def execute(self):
        """Execute method asociated to route
        """
        if (self.status == 'started'):
            if self.step.method:
                self.step.method(self, **self.step.method_pars)
                if hasattr(self, 'thread'):
                    self.status = 'ongoing'
                else:
                    self.status = 'done'

    def cancel(self):
        """Cancel execution of action
        """
        if self.status == 'ongoing':
            self.thread.cancel()
        self.status = 'cancelled'
        self.finished_on = datetime.datetime.now()


class Operation(Flow):
    """Add value stream action over a batch
    """
    def __init__(self, route, responsible, update=None):
        super().__init__(responsible, update)
        self.route = route

        self.actions = []
        self._cancel = False
        self.on_action = None

    def start(self, **inputs):
        super().start()
        self.inbox = inputs
        for att, value in inputs.items():
            setattr(self, att, value)

    @property
    def docs(self):
        if not hasattr(self, '_docs'):
            self._docs = []

        return self._docs

    def execute(self):
        """Execute method asociated to route
        """
        if (self.status == 'started'
                or self.status == 'walked'):
            if self.route.method:
                self.route.method(self, **self.route.method_pars)
                if hasattr(self, 'thread'):
                    self.status = 'ongoing'
            self.status = 'done'

    def walk(self):
        """Execute each child action
        """
        self.status = 'walking'
        self.on_action = None
        for action in self.action_iterator():
            if action:  # step could no create operation!
                self.on_action = action
                self.actions.append(action)
                action.start(**self.inbox)
                action.execute()
                if action.status == 'ongoing':
                    action.thread.join()
                    if hasattr(action, 'exception'):
                        # The thread has raised an exception
                        raise action.exception
                    action.status = 'done'
                action.close()
            self.on_action = None

        self.status = 'walked'

    def action_iterator(self):
        for step in self.route.steps:
            if self._cancel:
                break
            else:
                yield step.implement(self)

    def cancel(self):
        """Cancel execution of operation
        """
        if self.status == 'ongoing':
            self.thread.cancel()
        elif self.status == 'walking':
            self._cancel = True
        if self.on_action:
            self.on_action.cancel()
        self.status = 'cancelled'
        self.finished_on = datetime.datetime.now()

    def ask(self, key, **kwargs):
        self.question = Question(update=self.update)
        self.question.ask(key, **kwargs)

    def answer(self, **kwargs):
        self.question.answer(**kwargs)


class Route(Path):
    """Planning of an operation over resources
    """
    def __init__(self, role, source=None, destination=None,
                 outputs=None, parent=None,
                 method_name=None, method_pars=None):
        """Create route from planned inputs and outputs, can be embebed
        """
        self.parent = parent
        self.role = role
        self.sequence = 0
        self.source = source
        self.destination = destination
        self.steps = []

        self.outputs = outputs if outputs else []
        self.method_pars = method_pars if method_pars else {}

    def implement(self, responsible, update=None):
        """Returns operation instance from parent or responsible
        """
        return self.can_implement(Operation, responsible, update)

    def can_implement(self, Implementation, responsible, update):
        if not self.is_authorized(responsible):
            raise NotAuthorizedException(
                'Responsible {} can not execute flow'.format(responsible.description)
            )
        return Implementation(self, responsible, update)

    def is_authorized(self, responsible):
        """
        """
        return (responsible == self.role) or (self.role in responsible.roles)


class Step(Path):
    """Planning of a sub action for a Route
    """
    def __init__(self, route, method_name, method_pars):
        self.route = route
        self.sequence = 0 if not route.steps else route.steps[-1].sequence + 5
        self.method_name = method_name
        self.method_pars = method_pars if method_pars else {}
        self.outputs = []

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
