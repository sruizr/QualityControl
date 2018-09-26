import threading
import sys
from queue import Queue
import quactrl.models.operations as ops
import quactrl.models.quality as qua
from quactrl.models.devices import DeviceContainer


class NotFoundPart(Exception):
    pass


class TestingService:
    """Create and manage tests"""
    def __init__(self, persistence):
        self.persistence = persistence

        self.events = []
        self.inspectors = []
        self.location_key = None


    @property
    def cavities(self):
        return len(self.testers)

    @property
    def tests(self):
        """List tests by cavity"""
        return [None if self.inspectors is None
                else tester.test
                for tester in self.testers]

#     def setup(self, location_key, process_key, cavities=1,
#               create_part=False, till_first_failure=True):
#         """Setup Manager with running variables"""
#         self.tff = till_first_failure
#         self.location_key = location_key
#         self.process_key = process_key
#         self.location_key = location_key
#         self.create_part = create_part

#         self.dev_manager.load_devs_from(location_key)

#         for tester in self.testers:
#             if tester.is_alive():
#                 tester.stop()

#         self.testers = [Tester(self) for _ in range(cavities)]
#         self.events = [[] for _ in range(cavities)]


#     def start_test(self, part_info, responsible_key, cavity=1):
#         """Start test from part_information, responsible and other process parameters"""
#         tester = self.testers[cavity - 1]
#         tester.orders.put((part_info, responsible_key))

#     def stop(self, cavity=None):
#         """Stop a concrete tester or all testers"""
#         pending_orders = []

#         if cavity is None:
#             for tester in self.testers:
#                 if tester:
#                     pending_orders.extend(tester.stop())

#             self.testers = [Tester(self) for _ in range(self.cavities)]
#         else:
#             tester = self.testers[cavity - 1]
#             if tester:
#                 pending_orders.extend(tester.stop())
#             self.testers[cavity - 1] = Tester(self)
#         return pending_orders

#     def notify(self, info, cavity=1):
#         """Transfer notification from client to tester"""
#         self.testers[cavity - 1].notify(info)

#     def download_events(self, cavity=None):
#         """Get events from tester and store them to manager.events"""
#         events = []

#         if cavity is None:
#             for _cavity in range(self.cavities):
#                 events.append(self.download_events(_cavity + 1))
#         elif self.testers[cavity - 1]:
#                 events = self.testers[cavity - 1].empty_events()
#                 self.events[cavity - 1].extend(events)
#         return events


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
            self.route = self.db.Routes().get_by_part_model(self.part_model)

    def run(self):
        """Thread activation processing order by order"""
        while not self._stop_event.is_set():
            order = self.orders.get()
            if order is None:
                self.orders.task_done()
                break
            else:
                self.process_test(order)
                self.orders.task_done()

    def process_test(self, order):
        """Process a full test  from an order
        """
        part_info, responsible_key = order
        part = self.db.Parts().get_or_create(
            part_info['part_number'], part_info['tracking'],
            self.location)

        self.set_responsible_by(responsible_key)
        self.set_route_for(part)

        self.test = test = self.route.create_operation(self.responsible)
        self.db.Tests().add(test)

        test.start(subject=part, observer=self,
                   dev_container=self.dev_container,
                   cavity=self.cavity, tff=self.service.tff)
        try:
            test.walk()
            test.execute()
            test.close()
        except Exception as e:
            self.update('exception', e)
            test.cancel()
        finally:
            self.db.Session().commit()

    def update(self, obj, message, *args):
        """Receive from test notications of states
        """
        self.events.put((obj, message, *args))

    def stop(self):
        """Stop thread and return unprocessed orders"""
        pending_orders = []

        if self.orders.qsize() != 0:
            while not self.orders.empty():
                pending_orders.append(self.orders.get())
        self.orders.put(None)

        return pending_orders
