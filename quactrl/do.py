from quactrl import (
                     Column, ForeignKey, relationship, Model, dal
)


class Batch:
    def __init__(self, part_number, batch_number, operator):
        self.part_number = part_number
        self.batch_number = batch_number
        self.operator = operator
        self.close_date = None
        self.items = {}


class Item:
    def __init__(self, serial_number, batch):
        self.batch = batch
        self.sn = serial_number
        self.status = None
        self.tests = []

    def validate(self, serial_number):
        pass

    @classmethod
    def has_passed_test(self, serial_number):
        return False


class Test(Model):
    sample = Column(Integer)
    operator = Column(String)
    checks = []
    open_date = Column(datetime)

    def __init__(self, test_plan, sample, operator):
        sel
        for control in test_plan.controls:
            check = Check(self, control)


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
    __tablename__ = 'measurements'
    check = Column(Integer)
    value = Column(Float)
    index = Column(Integer)
    characteristic = Column(Integer)


class Failure(Model):
    __tablename__ = 'failures'
    check = Column(Integer)
    failure_mode = Column(Integer)
    key = Column(String)


class Check(Model):
    __tablename__ = 'checks'
    control = Column(Integer)
    test = Column(Integer)
    result = Column(Integer)

    failures = relationship('dnfas')
    measurements = relationship()

    def __init__(self, test, control):
        self.test = test
        self.control = control

        self.result = 'Pending'
        self.failures = []

    def report_failure(self, failure):
        self.failures.append(failure)
        self.result = 'NOK'

    def execute(**kwargs):
        pass


class DoDAO:
    """Class to operate with Do Objects"""
    pass
