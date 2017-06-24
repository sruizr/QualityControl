from enum import Enum
from quactrl import (
    Column, ForeignKey, relationship, Model,
    dal, Integer, String, DATETIME, DECIMAL, method_directory
)
from datetime import datetime
import pdb


class Result(Enum):
    PENDING = 0
    SUSPICIOUS = 1
    NOK = 2
    OK = 3


class Test(Model):

    __tablename__ = 'test'
    sample = Column(Integer)
    actor = Column(String)
    checks = []
    # open_date = Column(Datetime)

    def __init__(self, test_tree, sample, operator):
        self.test_tree = test_tree
        self.sample = sample
        self.actor = operator

        dal.session.commit()

    def run_test(self):
        try:
            for check in self.checks:
                check.execute()
        finally:
            self.result = self.eval()
            dal.session.commit()

    def eval(self):
        results = set([check.eval() for check in self.checks])

        if 'Pending' in results:
            return 'Pending'
        if 'NoOk' in results:
            return 'NoOk'
        if 'Suspicious' in results:
            return 'Suspicious'

        return 'OK'


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
        self.method()
        self.process_results()
        if observer:
            observer.update(self)
        self.close_date = datetime.now()

