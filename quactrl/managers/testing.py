import threading
from queue import Queue
from quactrl.domain.persistence import dal
import quactrl.domain.queries as qry
from quactrl.managers.devices import DeviceManager
from quactrl.managers import Event, Manager
from quactrl.domain.flows import Creation
from quactrl.domain.flows import Test, Check
from quactrl.helpers.managers import StoppableThread
from quactrl.domain.items import Part
from quactrl.domain.resources import PartModel


class NotFoundPart(Exception):
    pass


class TestManager(Manager):
    """Create and manage tests"""
    def __init__(self):
        Manager.__init__(self)
        self.events = []
        self.testers = []
        self.dev_manager = DeviceManager()
        self.location_key = None

    @property
    def cavities(self):
        return len(self.testers)

    @property
    def tests(self):
        """List tests by cavity"""
        return [None if tester is None
                else tester.test
                for tester in self.testers]

    def connect(self, **kwargs):
        """Connect to database"""
        dal.connect(**kwargs)

    def setup(self, location_key, process_key, cavities=1,
              create_part=False, till_first_failure=True):
        """Setup Manager with running variables"""
        self.tff = till_first_failure
        self.location_key = location_key
        self.process_key = process_key
        self.location_key = location_key

        self.dev_manager.load_devs_from(location_key)

        for tester in self.testers:
            if tester.is_alive():
                tester.stop()

        self.testers = [Tester(self) for _ in range(cavities)]
        self.events = [[] for _ in range(cavities)]


    def start_test(self, part_info, responsible_key, cavity=0):
        """Start test from part_information, responsible and other process parameters"""
        tester = self.testers[cavity]
        tester.orders.put((part_info, responsible_key))

    def stop(self, cavity=None):
        pending_orders = []

        if cavity is None:
            for tester in self.testers:
                if tester:
                    pending_orders.extend(tester.stop())

            self.testers = [Tester(self) for _ in range(self.cavities)]
        else:
            tester = self.testers[cavity]
            if tester:
                pending_orders.extend(tester.stop())
            self.testers[cavity] = Tester(self)
        return pending_orders

    def notify(self, info, cavity=0):
        """Transfer notification from client to tester"""
        self.testers[cavity].notify(info)

    def download_events(self, cavity=None):
        """Get events from tester and store them to manager.events"""
        events = []
        if cavity is None:
            for _cavity in range(self.cavities):
                events.append(self.download_events(_cavity))
        elif self.testers[cavity]:
                events = self.testers[cavity].empty_events()
                self.events[cavity].extend(events)
        return events


class Feedback(threading.Event):
    def __init__(self, template):
        super().__init__()
        self.template = template

    def answer(self, data):
        for field in self.template:
            if field not in data:
                self.set()
                raise Exception('Lack of {} information'.format(field))

        self.data = data
        self.set()


class Tester(StoppableThread):
    def __init__(self, manager, cavity=1):
        super().__init__()

        # Inherited properties from manager
        self.location = qry.get_location(manager.location_key)
        self.process = qry.get_process(manager.process_key)
        self.dev_manager = manager.dev_manager
        self.ttf = manager.ttf
        self.create_part = manager.create_part

        self.cavity = cavity

        self.events = Queue()
        self.orders = Queue()

        self.responsible = None
        self.open_check = None
        self.cancel_signal = False
        self.control_plan = None

    def loop(self):
        """One cycle loop for tester"""
        order = self.orders.get()
        if order is not None:
            self.process_test(order)

    def stop(self):
        """Stop thread and return unprocessed orders"""
        pending_orders = []

        if self.orders.qsize() != 0:
            while not self.orders.empty():
                pending_orders.append(self.orders.get())
        self.stop_event.set()
        self.orders.put(None)

        return pending_orders

    def cancel_test(self):
        self.cancel_signal = True
        if self.open_check is not None:
            self.open_check.result = 'cancelled'
            self.open_check.finished.set()

    def _get_or_create_part(self, part_info):
        part_number = part_info.gent('part_number')
        serial_number = part_info['serial_number']
        part = qry.get_part(part_number=part_number, location=self.location,
                            serial_number=serial_number)
        if part is None and self.create_part:
            part = None  #  TODO

        return part

    def process_test(self, order):
        self.session = session = dal.Session()

        part_info, responsible_key = order

        part = self.get_or_create_part(part_info, self.location)

        self.set_responsible_by(responsible_key)
        self.set_control_plan_for(part, self.process)

        test = self.control_plan.create_flow(self.responsible)
        test.start(part=part)
        session.add(test)
        self.events.put(Event('test_started', testy))

        for control in self.control_plan.steps:
            check = control.create_flow(test, self.responsible)
            session.add(check)

            self.events.put(Event('check_started', check, cavity=self.cavity))

            check.prepare()
            check.dev_manager = self.dev_manager
            check.tester = self

            if self.cancel_signal:
                check.state = 'cancelled'
                self.events.put(Event('test_finished', check, cavity=self.cavity))
            else:
                try:
                    check.execute()
                    if check.result == 'ongoing':
                        self.open_check = check
                        self.events.put(Event('ongoing', check,
                                              cavity=self.cavity))
                        check.finished = threading.Event()
                        check.finished.wait()
                        self.open_check = None

                except Exception:
                    check.result = 'cancelled'
                    self.cancel_signal = True

                if check.result != 'cancelled':
                    self.events.put(Event('finish_test', check,
                                          cavity=self.cavity))
                else:
                    self.events.put(Event('cancel_test', check, cavity=self.cavity))

                check.terminate()

        test.execute()
        test.terminate()
        self._current_check = None

        self.session = dal.Session()
        self.session.add(test)
        self.session.commit()

        self.events.put(Event('finish_test', test, cavity=self.cavity))
        self.cancel_signal = False

    def request_feedback(self, template):
        self.events.put(Event('feedback_request', template,
                              cavity=self.cavity))
        # Event for waiting
        self.feedback = Feedback(template)
        self.feedback.wait()

        self.events.put(Event('feedback_process', self.feedback.data,
                              cavity=self.cavity))
        return self.feedback.data

    def set_responsible_by(self, key):
        if self.responsible is None or self.responsible.key != key:
            self.responsible = qry.get_responsible_by(key=key)

    def set_control_plan_for(self, part):
        if (
                self.control_plan is None
                or not self.control_plan.has_output(part.part_model)
        ):
            self.control_plan = qry.get_control_plan_by(
                location=self.location,
                process=self.process,
                part_model=part.part_model)

    def cancel(self):
        self.cancel_signal = True


    def notify(self):
        """Recieve notifications from observables and records it as events"""
        pass
