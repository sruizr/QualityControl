from enum import Enum
from threading import Thread, Event
from quactrl import (
    Column, ForeignKey, relationship, Model,
    dal, Integer, String, DATETIME, DECIMAL, method_directory
)
from quactrl.domain.erp import (Item, Resource)
from datetime import datetime
import pdb


class Result(Enum):
    PENDING = 0
    ONGOING = 1
    SUSPICIOUS = 2
    NOK = 2
    CANCELLED = 8
    OK = 10


class Sampling(enum.Enum):
    ongoing = 0
    every_unit = 1

    each_10 = 21
    each_100 = 22
    each_1000 = 23
    each_10000 = 24
    each_100000 = 25

    by_second = 30
    by_minute = 31
    by_hour = 32
    by_day = 33
    by_week = 34
    by_month = 35
    by_year = 36



class Test(Item):
    __mapped_args__ = {'polimorphic__tablename__ = 'test'
    sample = Column(Integer)

    verifier = Column(String)
    state = Column(Integer)
    checks = []
    # open_date = Column(Datetime)

    def __init__(self, verifier, process, control_plan):
        self.verifier = verifier
        self.process = process
        self.state = Result.PENDING
        for control in self.controls:
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


class Check(Item):
    __mapper_args__ = {'polymorphic_identity': 'check'}


class Measurement(Model):
    __mapper_args__ = {'polymorphic_identity': 'measurement'}

    check_id = Column(Integer, ForeignKey('check.id'))
    characteristic_id = Column(Integer, ForeignKey('characteristic.id'))
    value = Column(DECIMAL)
    index = Column(Integer)


class Failure(Item):
    __mapper_args__ = {'polymorphic_identity': 'failure'}


class Check(Model):
    __tablename__ = 'check'
    control = Column(Integer)
    test_id = Column(Integer, ForeignKey('test.id'))
    result = Column(Integer)
    state = Column(Integer)


    failures = relationship('Failure', backref='check')
    measures = relationship('Measurement', backref='check')

    def __init__(self, test, control):
        self.open_date = datetime.now()
        self.test = test
        self.control = control

        self.method = method_factory.get_method(control.method)

        self.state = Result.PENDING
        self.failures = []
        self.measures = dict()

    def add_failure(self, f_mode, characteristic, item, device):
        """Append failures to checks"""
        failure = Failure(f_mode, characteristic, item, device)
        self.failures.append(failure)

    def get_measure(self, characteristic, item=None, device=None):
        """Get stored measure from characteristic"""
        pass

    def add_measure(self, value, characteristic, item=None, device=None):
        """Append measurements to measures"""
        measure = Measure(value, characteristic, item, device)
        self.measures.append(measure)

    def process_results(self):
        """"Persist measures and failures and state final result of check"""
        if self.failures == []:
            self.state = Result.OK
        else:
            self.state = Result.NOK

    def close(self, observer=None):
        """Execute the check"""
        self.open_date = datetime.now()
        self.state = Result.ONGOING
        self.method()
        self.process_results()
        self.close_date = datetime.now()

class Measure(Model):
    characteristic_id = Column(Integer, ForeignKey('characteristic.id'))
    value = Column(Decimal)
    part_id = Column(Integer, ForeingKey('resource.id'))
    device_id = Column(Integer, ForeingKey('node.id'))
    measured_on = Column(datetime, default=datetime.now)
