import threading
from queue import Queue
from quactrl.domain.persistence import dal
import quactrl.domain.queries as qry
from quactrl.managers.devices import DeviceManager
from quactrl.managers import Event, Manager, Feedback
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
        self.create_part = create_part

        self.dev_manager.load_devs_from(location_key)

        for tester in self.testers:
            if tester.is_alive():
                tester.stop()

        self.testers = [Tester(self) for _ in range(cavities)]
        self.events = [[] for _ in range(cavities)]


    def start_test(self, part_info, responsible_key, cavity=1):
        """Start test from part_information, responsible and other process parameters"""
        tester = self.testers[cavity - 1]
        tester.orders.put((part_info, responsible_key))

    def stop(self, cavity=None):
        """Stop a concrete tester or all testers"""
        pending_orders = []

        if cavity is None:
            for tester in self.testers:
                if tester:
                    pending_orders.extend(tester.stop())

            self.testers = [Tester(self) for _ in range(self.cavities)]
        else:
            tester = self.testers[cavity - 1]
            if tester:
                pending_orders.extend(tester.stop())
            self.testers[cavity - 1] = Tester(self)
        return pending_orders

    def notify(self, info, cavity=1):
        """Transfer notification from client to tester"""
        self.testers[cavity - 1].notify(info)

    def download_events(self, cavity=None):
        """Get events from tester and store them to manager.events"""
        events = []

        if cavity is None:
            for _cavity in range(self.cavities):
                events.append(self.download_events(_cavity + 1))
        elif self.testers[cavity - 1]:
                events = self.testers[cavity - 1].empty_events()
                self.events[cavity - 1].extend(events)
        return events


class Tester(StoppableThread):
    def __init__(self, manager, cavity=1):
        super().__init__()

        # Inherited properties from manager
        self.location = qry.get_location(manager.location_key)

        self.process = qry.get_process_by(manager.process_key)
        self.dev_manager = manager.dev_manager

        self.tff = manager.tff
        self.create_part = manager.create_part

        self.cavity = cavity

        self.events = Queue()
        self.orders = Queue()

        self.responsible = None
        self.open_check = None
        self.cancel_signal = False
        self.control_plan = None
        self.feedback = None
        self.test = None
        self._current_check = None

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

    def get_or_create_part(self, part_info):
        part_number = part_info.get('part_number')
        serial_number = part_info['serial_number']
        part = qry.get_part(part_number=part_number, location=self.location,
                            serial_number=serial_number)
        if part is None and self.create_part:
            creation = Creation(self.responsible)
            part_model = qry.get_part_model_by(part_number)
            part = Part()
            part.resource = part_model
            part.tracking = serial_number
            part.qty = 1.0
            creation.run(self.location, part)

        return part

    def process_test(self, order):
        session = dal.Session()

        part_info, responsible_key = order

        part = self.get_or_create_part(part_info, self.location)

        self.set_responsible_by(responsible_key)
        self.set_control_plan_for(part)

        self.test = test = self.control_plan.create_flow(self.responsible)
        test.start(part=part)
        session.add(test)
        test.tester = self

        self._current_check = None
        for control in self.control_plan.steps:
            if self.cancel_signal:
                test.cancel()
                break

            if control.pars.get('pre_feedback'):
                data = control.pars.get('pre_feedback')
                self.request_feedback(**data)

            self._current_check = check = control.create_flow(test,
                                                              self.responsible)
            check.tester = self
            check.dev_manager = self.dev_manager

            session.add(check)
            check.run()

            if control.pars.get('post_feedback'):
                data = control.pars.get('post_feedback')
                self.request_feedback(**data)

        test.execute()
        test.terminate()

        session.commit()

        self._current_check = None
        self.cancel_signal = False

    def update(self, obj):
        """Recieve notifications from observables and record it as events"""
        _type = {'Test': 'test', 'Check': 'check'}

        finished_states = ['ok', 'incorrect', 'ng', 'suspicious', 'nok']
        if obj.state in finished_states:
            signal = 'finished'
        else:
            signal = obj.state

        signal = '{}_{}'.format(_type[obj.__class__.__name__], signal)
        self.events.put(Event(signal, obj))

    def request_feedback(self, message, answer_fields=None):
        self.feedback = Feedback(message, answer_fields)

        self.events.put(Event('feedback_requested', self.feedback))

        # Feedback is waiting till is answered by other instance
        self.feedback.wait()

        self.events.put(Event('feedback_answered', self.feedback))
        return self.feedback.data

    def answer_feedback(self, data):
        self.feedback.answer(data)

    def set_responsible_by(self, key):
        if self.responsible is None or self.responsible.key != key:
            self.responsible = qry.get_responsible_by(key=key)

    def set_control_plan_for(self, part):

        if (
                self.control_plan is None
                or not self.control_plan.validate_resource(part.part_model)
        ):
            self.control_plan = qry.get_control_plan_by(
                location=self.location,
                process=self.process,
                part_model=part.part_model)

    def cancel_test(self):
        self.cancel_signal = True
        if self._current_check is not None and self._current_check.state == 'ongoing':
            """There is a check with a thread started"""
            self._current_check.cancel()

    def empty_events(self):
        events = []
        for _ in range(self.events.qsize()):
            events.append(self.events.get())
        return events
