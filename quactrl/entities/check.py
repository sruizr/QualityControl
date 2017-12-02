from enum import Enum
from threading import Thread, Event
from quactrl import (
    Column, ForeignKey, relationship, Model,
    dal, Integer, String, DATETIME, DECIMAL, method_directory
)
from quactrl.factories import ms_factory, method_factory
from datetime import datetime
import pdb


class Result(Enum):
    PENDING = 0
    ONGOING = 1
    SUSPICIOUS = 2
    NOK = 2
    CANCELLED = 8
    OK = 10


class TestManager:
    """It handles tests in paralllel and load  test plans"""
    pass


class Test(Model):

    __tablename__ = 'test'
    sample = Column(Integer)

    verifier = Column(String)
    state = Column(Integer)
    checks = []
    # open_date = Column(Datetime)

    def __init__(self):
        self.verifier = verifier
        self.sample = sample
        self.state = Result.PENDING
        for control in controls:
            check = Check(self, control)
            self.checks.append(check)

        self.session = dal.Session()
        self.session.add(self)
        self.session.commit()

        self.current_check_index = None
        self.observers = []

    def execute(self):
        """Run sequence of tests sequentially"""

        if self.current_check_index is None:
            self.current_check_index = 0

        try:
            check = self.checks[self.current_check_index]
            check.execute()
        except Exception as e:
            self.close()
            raise e

    def update(self, check, progress=100):
        self.notify(check, progress)

        if self.state == Result.CANCELLED:
            return None

        if progress == 100:
            self.current_check_index += 1
            if self.current_check_index == len(self.checks):
                # check sequence  is finished
                self.current_check_index = None
                self.close()
            else:
                self.execute()

    def notify(self, check, progress):
        for observer in self.observers:
            observer.update(chek, progress)

    def eval(self):
        results = set([check.state for check in self.checks])

        if results == set([Result.PENDING]):
            return Result.PENDING

        if Result.NOK in results:
            return Result.NOK

        if Result.PENDING in results:
            return Result.ONGOING

        if Result.SUSPICIOUS in results:
            return Result.SUSPICIOUS

        if results == set([Result.OK]):
            return Result.OK

    def cancel(self):
        self.close(Result.CANCELLED)

    def close(self, state=None):
        if state is None:
            state = self.eval()

        if state == Result.ONGOING:
            state = Result.CANCELLED

        self.state = state
        self.close_date = datetime.now()
        self.session.commit()


class Measurement(Model):
    __tablename__ = 'measurement'
    check_id = Column(Integer, ForeignKey('check.id'))
    characteristic_id = Column(Integer, ForeignKey('characteristic.id'))
    value = Column(DECIMAL)
    index = Column(Integer)


class Failure(Model):
    __tablename__ = 'failure'
    check_id = Column(Integer, ForeignKey('check.id'))
    mode = Column(String)
    characteristic_id = Column(Integer, ForeignKey('characteristic.id'))
    characteristic = relationship('Characteristic')

    def __init__(self, mode, characterisc, index=None):
        self.mode = mode
        self.characteristic = characterisc
        self.index = index


class Sample:
    pass


class MethodFactory:
    def __init__(self, method_directory):
        self.method_directory = method_directory

    def get_method(self, name):
        def none_method(check):
            pass

        return none_method

method_factory = MethodFactory(method_directory)

class Check(Model):
    __tablename__ = 'check'
    control = Column(Integer)
    test = Column(Integer, ForeignKey('test.id'))
    result = Column(Integer)
    state = Column(Integer)

    failuresss = relationship('Failure', backref='check')
    measuresss= relationship('Measurement', backref='check')

    def __init__(self, test, control):
        self.test = test
        self.control = control

        self.method = method_factory.get_method(control.method)

        self.state = Result.PENDING
        self.failures = []
        self.measures = dict()

    def eval_measure(self, value, characteristic, uncertainty=0):
        """Eval a measure comparing to characteristic limits"""

        if hasattr(characteristic, 'modes'):
            modes = characteristic.modes
        else:
            modes = ['low', 'high']
        # pdb.set_trace()
        failure = None

        self.add_measure(value, characteristic)
        limits = characteristic.limits

        index = 0
        if type(self.measures[characteristic]) is list:
            index = len(self.measures[characteristic])- 1

        if type(limits[0]) is not list:
            if limits[1] is not None:
                if value > limits[1] - uncertainty:
                    failure = Failure(modes[1] + '?', characteristic, index)
                if value > limits[1]:
                    failure = Failure(modes[1], characteristic, index)

            if limits[0] is not None:
                if value < limits[0] + uncertainty:
                    failure = Failure(modes[0] + '?', characteristic, index)
                if value < limits[0]:
                    failure = Failure(modes[0], characteristic, index)

        if failure:
            self.failures.append(failure)

    def add_measure(self, value, characteristic):
        """Append measurements to measures"""

        if hasattr(characteristic, 'limits'):
            limits = characteristic.limits
        else:
            CharacteristicValueError('{} is not value characteristic'.
                                     formate(characteristic))

        if characteristic in self.measures.keys():
            prev_value =  self.measures[characteristic]
            if type(prev_value) is list:
                self.measures[characteristic].append(value)
            else:
                self.measures[characteristic] = [prev_value, value]
        else:
            self.measures[characteristic] = value

    def process_results(self):
        """"Persist measures and failures and state final result of check"""
        if self.failures == []:
            self.state = Result.OK
        else:
            self.state = Result.NOK

    def execute(self, observer=None):
        """Execute the check"""
        self.open_date = datetime.now()
        self.state = Result.ONGOING
        self.method()
        self.process_results()
        self.close_date = datetime.now()


class Inspector:
    def __init__(self, inspector_manager):
        """

        """
        self.env = inspector_manager.env
        self.device_fry = self.inspector_manager.env.device_fry
        self.part = None
        self.part_input = Event()
        self.end_batch = False

    def run(self):
        """Waits to have a part"""
        while not self.end_batch:
            self.part_input.wait()
            for control in self.controls:
                if control.part_needs_check(part):
                    failures = control.check()
