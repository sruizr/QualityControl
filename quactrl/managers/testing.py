import threading
from queue import Queue
from quactrl.domain.persistence import dal
import quactrl.domain.queries as qry
from quactrl.managers.devices import DeviceManager
from quactrl.managers import Event
from quactrl.domain.flows import Creation
from quactrl.domain.flows import Test, Check


class TestManager:
    """Create and manage tests"""
    def __init__(self):
        self.events = Queue()
        self.testers = []
        self.dev_manager = DeviceManager()
        self.location = None

    @property
    def tests(self):
        """List tests by cavity"""
        return [None if tester is None
                else tester.test
                for tester in self.testers]

    def set_database(self, connection_string):
        """Connects database"""
        dal.connect(connection_string)

    def go_to(self, location):
        """Load all devices from location"""
        self._location = location
        self.dev_manager.load_devs_from(location)

    def start_test(self, part_info, responsible, **test_pars):
        """Start test from part_information, responsible and other process parameters"""
        cavity = test_pars.pop('cavity', 1)
        # Amplified testers from cavity information

        tester = self._get_tester(cavity)
        tester.orders.put((part_info, responsible, test_pars))

    def _get_tester(self, cavity):
        """Lazy loading of testers"""
        if cavity > len(self.testers):
            for _ in range(cavity - len(self.testers)):
                self.testers.append(None)

        index = cavity - 1
        if self.testers[index] is None:
            tester = Tester(self)
            tester.start()
            self.testers[index] = tester

        return tester

    def stop(self, cavity=None):
        pending_pars = []

        if cavity is None:
            for tester in self.testers:
                if tester:
                    pending_pars.extend(tester.stop())
        else:
            tester = self.testers[cavity-1]
            if tester:
                pending_pars.extend(tester.stop())
        return pending_pars


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


class Tester(threading.Thread):
    def __init__(self, manager, cavity=1):
        super().__init__()
        self.location = manager.location
        self.dev_manager = manager.dev_manager
        self.events = manager.events
        self.orders = Queue()
        self.responsible = None
        self.stop_signal = False
        self.cancel_signal = False
        self.control_plan = None
        self.responsible = None
        self.open_check = None
        self.cavity = cavity

    def run(self):
        while not self.stop_signal:
            order = self.orders.get()
            if order is not None:
                self.process(order)

    def stop(self):
        pending_pars = []
        self.stop_signal = True

        if self.orders.qsize() == 0:
            self.orders.put(None)
        else:
            while not self.orders.empty():
                part_info, _, _ = self.orders.get()
                pending_pars.append(part_info)

    def cancel_test(self):
        self.cancel_signal = True
        if self.open_check is not None:
            self.open_check.result = 'cancelled'
            self.open_check.finished.set()

    def _get_or_create_part(self, part_info, location):
        pass

    def process(self, order):
        session = dal.Session()

        part_info, responsible_key, test_pars = order

        part = self._get_or_create_part(part_info, self.location)

        self.set_responsible_by(responsible_key)
        self.set_control_plan_for(part)

        test = Test(self.control_plan, self.responsible)
        test.set_input('part', part)
        session.add(test)
        self.events.put(Event('start', test, cavity=self.cavity))

        for control in self.control_plan.steps:
            check = Check(test, control, self.responsible)
            session.add(check)
            self.events.put(Event('start', check, cavity=self.cavity))

            check.prepare()
            check.dev_manager = self.dev_manager
            check.tester = self

            if self.cancel_signal:
                self.events.put(Event('cancel', check, cavity=self.cavity))
                check.result = 'cancelled'
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
                    self.events.put(Event('finish', check,
                                          cavity=self.cavity))
                else:
                    self.events.put(Event('cancel', check, cavity=self.cavity))

                check.terminate()

        test.execute()
        test.terminate()
        self._current_check = None

        self.session = dal.Session()
        self.session.add(test)
        self.session.commit()

        self.events.put(Event('finish', test, cavity=self.cavity))
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
            self.responsible = dal.get_responsible_by(key=key)

    def set_control_plan_for(self, part):
        if (
                self.control_plan is None
                or not self.control_plan.has_output(part.resource)
        ):
            self.control_plan = dal.get_control_plan_by(self.location,
                                                        part.resource)

    def cancel(self):
        self.cancel_signal = True
