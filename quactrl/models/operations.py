import datetime
import sys
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
    def __init__(self, responsible):
        self.responsible = responsible
        self.motions = []
        self.started_on = None
        self.finished_on = None

    def start(self):
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

    def finish(self):
        self.finished_on = datetime.datetime.now()


class Part:
    """Part with unique serial number
    """
    def __init__(self, model, tracking, location=None):
        self.model = model
        self.tracking = tracking
        self.location = location
        self.defects = []
        self.measures = []


class IncorrectOperationState(Exception):
    pass


class Operation(Handling):
    """Add value stream action over a batch
    """
    def __init__(self, route, parent=None, responsible=None):
        if responsible is None and parent is None:
            raise Exception()

        self.route = route
        self.responsible = responsible

        self.parent = parent
        if parent:
            self.parent.add_action(self)
            self.responsible = parent.responsible

        super().__init__(self.responsible)
        self.operations = []
        self.inbox = {}
        self.outbox = {}
        self.udpate = None
        self._state = 'open'
        self._cancel = False
        self.on_op = None

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state
        if self.udpate:
            self.update(state, self)

    def start(self, **inputs):
        super().start()
        self.update = inputs.get('update')
        self.cavity = inputs.get('cavity')

        self.inbox.update(inputs)
        self.state = 'started'

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
                op.start(update=self.update, **self.inbox)
                try:
                    op.execute()
                    if op.state == 'ongoing':
                        op.thread.join()
                    op.close()
                except Exception as e:
                    if self.update:
                        self.update(*sys.exc_info())
                    raise e

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
    def __init__(self, role, source=None, destination=None,
                 outputs=None, parent=None,
                 method=None, method_pars=None):
        """Create route from planned inputs and outputs, can be embebed
        """
        self.parent = parent
        self.sequence = 0
        self.source = source
        self.destination = destination
        self.steps = []

        if parent:
            self.sequence = (parent.steps[-1].sequence + 5
                             if parent.steps else 0)
            parent.steps.append(self)

        self.outputs = outputs if outputs else []
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


class Step:
    """Planning of a sub action for a Route
    """

    def __init__(self, route, method, method_pars):

        self.route = route
        self.method = method
        self.method_pars = method_pars if method_pars else {}
