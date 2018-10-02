import threading
import sys
from queue import Queue
import quactrl.models.operations as ops
import quactrl.models.quality as qua
from quactrl.models.devices import DeviceContainer


class NotFoundPart(Exception):
    pass


class InspectorException(Exception):
    pass


class TestingService:
    """Test parts from a location"""
    def __init__(self, database):
        self.db= database

        self.events = {}
        self.inspectors = {}
        self.location_key = None
        self.dev_container = DeviceContainer(self.db.DeviceDefs())

    @property
    def cavities(self):
        return len(self.inspectors)

    @property
    def tests(self):
        """List tests by cavity"""
        return {cavity: inspector.test
                for cavity, inspector in zip(self.active_cavities, self.inspectors)
        }

    def setup(self, location_key, cavities=None, till_first_failure=True):
        """Setup Manager with running variables"""
        self.tff = till_first_failure
        self.location_key = location_key

        self.dev_container.set_location(location_key)

        for inspector in self.inspectors.values():
            if inspector.is_alive():
                raise InspectorException('Inspector {} is still alive, stop it before new setup'.format(inspector.name))
                inspector.stop()

        if cavities is None:
            self.active_cavities = [None]
        else:
            if type(cavities) is int:
                self.active_cavities = list(range(cavities))
            elif type(cavities) is list:
                self.active_cavities = cavities

        self.inspectors = {
            cavity: Inspector(self.db, self.dev_container, self.location_key,
                              cavity, till_first_failure)
            for cavity in self.active_cavities
        }

        for inspector in self.inspectors.values():
            inspector.start()

    def stack_test(self, part_info, responsible_key, cavity=None):
        """Start test from part_information, responsible and other process parameters"""
        inspector = self.inspectors[cavity]
        inspector.orders.put((part_info, responsible_key))

    def notify(self, info, cavity=None):
        """Transfer notification from client to inspector"""
        self.inspectors[cavity - 1].notify(info)

    def stop_inspector(self, cavity=None):
        """Stop a concrete inspector or all inspectors"""
        pending_orders = []

        if cavity is None:
            for inspector in self.inspectors:
                if inspector:
                    pending_orders.extend(inspector.stop())

            self.inspectors = [Inspector(self) for _ in range(self.cavities)]
        else:
            inspector = self.inspectors[cavity - 1]
            if inspector:
                pending_orders.extend(inspector.stop())
            self.inspectors[cavity - 1] = Inspector(self)
        return pending_orders

    def get_events(self, cavity=None):
        """Get events from inspector and store them to manager.events"""
        events = []

        if cavity is None:
            for _cavity in range(self.cavities):
                events.append(self.download_events(_cavity + 1))
        elif self.inspectors[cavity - 1]:
                events = self.inspectors[cavity - 1].empty_events()
                self.events[cavity - 1].extend(events)
        return events

    def restart_inspector(self, cavity=None):
        pending_orders = self.inspectors[cavity].stop()
        inspector = Inspector(self.db, self.dev_container, self.location_key,
                              cavity, self.ttf)
        for order in pending_orders:
            inspector.orders.put(order)

        inspector.start()
        self.inspectors[cavity] = Inspector


class Inspector(threading.Thread):
    """Inspector of one unique part sharing some devices on a location
    """
    def __init__(self, database, dev_container, location_key,
                 cavity=None, tff=True):
        """Args:
        database(Container): Persistence layer container of providers
        dev_container(Container): Container of devices
        location_key: where is located the test station and all its devices
        cavity: cavity number, None is the station is not multicavity
        tff(Boolean): Till first failure, stops test when first failure is found
        """
        name = 'Inspector'
        if cavity is not None:
            name += '_{}'.format(cavity)
        super().__init__(name=name)
        self.db = database
        self.dev_container = dev_container
        self.location = self.db.Locations().get_by_key(location_key)
        self.cavity = cavity
        self.tff = tff

        # Inputs and Outputs of inspector
        self.orders = Queue()
        self.events = Queue()
        self.state = 'avalaible'

        # Batch variables
        self.responsible = None
        self.part_model = None
        self.route = None

        self._stop_event = threading.Event()

    def set_responsible(self, responsible_key):
        """Loads responsible if it has changed
        """
        if self.responsible is None or self.responsible.key != responsible_key:
            self.responsible = self.db.Persons().get_by_key(responsible_key)

    def set_route_for(self, part_number):
        if (
                self.part_model is None
                or self.part_model.part_number != part_number):
            self.part_model = self.db.PartModels().get_by_part_number(
                part_number)

        if (
                self.route is None
                or self.part_model in
                self.route.inputs['part_group'].part_models):
            self.route = self.db.Routes().get_by_part_model_and_location(
                self.part_model, self.location)

    def run(self):
        """Thread activation processing order by order"""
        while not self._stop_event.is_set():
            self.state = 'waiting'
            order = self.orders.get()
            if order is None:
                self.orders.task_done()
                break
            else:
                self.state = 'iddle'
                self.run_test(order)
                self.orders.task_done()

        self.state = 'stopped'

    def run_test(self, order):
        """Process a full test  from an order
        """
        part_info, responsible_key = order
        part = self.db.Parts().get_or_create(self.location, **part_info)
        self.set_responsible(responsible_key)
        self.set_route_for(part)

        self.test = test = self.route.create_operation(self.responsible)
        self.db.Tests().add(test)

        test.start(subject=part, dev_container=self.dev_container,
                   cavity=self.cavity, tff=self.tff, update=self.update)
        try:
            test.walk()
            test.execute()
            test.close()
        except Exception as e:
            self.update('exception', e)
            test.cancel()
            self.state = 'cancelled'
        finally:
            self.db.Session().commit()

    def update(self, state, obj, *args):
        """Receive from test notications of states
        """
        self.events.put((state, obj, *args))

    def stop(self):
        """Stop thread and return unprocessed orders"""
        pending_orders = []
        self._stop_event.set()

        if self.orders.qsize() != 0:
            while not self.orders.empty():
                pending_orders.append(self.orders.get())

        return pending_orders

    def ask(self, message, *args):
        question = Question()
        self.events.put(('waiting', question))
        question.ask(message, *args)
        return question


class Question(threading.Event):

    def ask(self, message, *args):
        self.request = (message, *args)
        self.wait()

    def answer(self, *args):
        self.response = [arg for arg in args]
        self.set()
