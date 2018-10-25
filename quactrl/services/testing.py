import threading
import traceback
from queue import Queue
from quactrl.models.devices import DeviceContainer
import quactrl.models.operations as op
from quactrl.models.quality import DefectFound
import sys


class NotFoundPart(Exception):
    pass


class InspectorException(Exception):
    pass


class Service:
    """Test parts from a location"""
    def __init__(self, database, location, cavities=None,
                 till_first_failure=True, sn_generator=None):
        self.db = database
        self.tff = till_first_failure
        self.location_key = location
        self.sn_generator = sn_generator
        self._production_orders = {}

        self.events = {}
        self.inspectors = {}

        all_devices = self.db.Devices().get_all_from(location)
        self.dev_container = DeviceContainer(all_devices)
        self._start_inspectors(cavities)

        self._production_orders = {}
        self._lock = threading.Lock()

    @property
    def cavities(self):
        return len(self.inspectors)

    @property
    def active_cavities(self):
        return list(self.inspectors.keys())

    @property
    def tests(self):
        """List tests by cavity"""
        return {cavity: inspector.test
                for cavity, inspector in self.inspectors.items()}

    def _start_inspectors(self, cavities):
        if cavities is None:
            active_cavities = [None]
        else:
            if type(cavities) is int:
                active_cavities = list(range(cavities))
            elif type(cavities) is list:
                active_cavities = cavities

        for cavity in active_cavities:
            inspector = Inspector(self.db, self.dev_container,
                                  self.location_key, cavity, self.tff,
                                  self.sn_generator)
            inspector.start()
            self.inspectors[cavity] = inspector

    def restart(self, cavities=None, clean_orders=False):
        """Restart inspectors
        """
        if cavities is None:
            cavities = self.active_cavities

        for cavity in cavities:
            pending_orders = self.stop(cavity)
            inspector = Inspector(self.db, self.dev_container,
                                  self.location_key, cavity, self.ttf,
                                  self.sn_generator)
            self.inspectors[cavity] = inspector
            inspector.start()
            if not clean_orders:
                for order in pending_orders:
                    inspector.orders.put(order)

    def stop(self, cavity=None):
        """Stop a concrete inspector or all inspectors"""
        pending_orders = []
        if cavity is None:
            for inspector in self.inspectors.values():
                if inspector:
                    pending_orders.extend(inspector.stop())
        else:
            if cavity in self.inspectors.keys():
                inspector = self.inspectors[cavity]
                pending_orders.extend(inspector.stop())

        return pending_orders

    def stack_part(self, part_info, responsible_key, cavity=None):
        """Start part for testing on an order process parameters"""
        inspector = self.inspectors[cavity]
        inspector.orders.put((part_info, responsible_key))

    def notify(self, info, cavity=None):
        """Transfer notification from client to inspector"""
        self.inspectors[cavity].notify(info)

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

    def get_last_events(self, cavity=None):
        pass

    def __del__(self):
        self.stop()


class Inspector(threading.Thread):
    """Inspector of one unique part sharing some devices on a location
    """
    def __init__(self, database, dev_container, location_key,
                 cavity=None, tff=True, sn_generator=None):
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
        self.location = self.db.Locations().get(location_key)
        self.cavity = cavity
        self.tff = tff
        self.sn_generator = sn_generator

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
            self.responsible = self.db.Persons().get(responsible_key)

    def set_route_for(self, part_number):
        if (
                self.part_model is None
                or self.part_model.part_number != part_number):
            self.part_model = self.db.PartModels().get(part_number)

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

    def get_part(self, part_info):
        """Get part from data layer if exist or create a new one
        """
        serial_number = part_info.pop('serial_number', None)
        if not serial_number:
            serial_number = self.sn_generator.get_serial_number(
                self.part_model.key,
                part_info.pop('batch_number')
            )

        part = self.db.Parts().get(self.part_model, serial_number)
        if part is None:
            part = op.Part(self.part_model, serial_number,
                           location=self.location)
        if part.location != self.location:
            raise Exception('Part found on incorrect location')

        connection = self.dev_container.modbus_conn()
        connection = connection if self.cavity is None \
            else connection[self.cavity]
        part.set_dut(connection)

    def run_test(self, order):
        """Process a full test  from an order
        """
        try:
            part_info, responsible_key = order
            self.set_responsible(responsible_key)
            self.set_route_for(part_info.pop('part_number'))
            part = self.get_part(part_info)

            self.test = test = self.route.implement(self.responsible,
                                                    self.update)
            self.db.Tests().add(test)
            test.start(part=part, dev_container=self.dev_container,
                       cavity=self.cavity)
            try:
                test.walk()
                test.execute()
                test.close()
            except DefectFound:
                if self.tff:
                    test.close()
            except Exception as e:
                trc = sys.exc_info()
                self.update('test_error', e, traceback.format_tb(trc[2]))
                test.cancel()
            finally:
                self.db.Session().commit()
        except Exception as e:
            trc = sys.exc_info()
            self.update('crash', e, traceback.format_tb(trc[2]))
            raise e

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
        else:
            self.orders.put(None)

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
