import datetime

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


class Route:
    """Planning of an operation on parts
    """
    def __init__(self, inputs, outputs, source, destination):
        self.steps = []



class Part(Batch):
    """Part with unique serial number
    """
    def __init__(self, **kwargs):
        super().__init__(qty=1, **kwargs)


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

        self.actions = []
        self.state = 'open'
        self._cancel = False

    def start(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
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

    def execute_actions(self):
        self.state = 'walking'
        for action in self.get_actions():
            self.current_action = action
            action.start()
            action.execute()
            if action.state == 'ongoing':
                action.thread.join()
            action.close()
            self.current_action = None
        self.state = 'started'

    def list_actions(self):
        for step in self.route.steps:
            if self._cancel:
                break
            else:
                yield step.create_action(self)

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
        self.state = 'cancelled'
        self.finished_on = datetime.datetime.now()
