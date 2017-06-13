from quactrl import (
    Column, ForeignKey, relationship, Model,
    dal, Integer, String, DATETIME, DECIMAL
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
    __tablename__='test'
    sample = Column(Integer)
    operator = Column(String)
    checks = []
    # open_date = Column(Datetime)

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

    def __init__(self, mode, characterisc):
        self.mode = mode
        self.characteristic = characterisc

class Sample:
    pass


class Check(Model):
    __tablename__ = 'check'
    control = Column(Integer)
    test = Column(Integer)
    result = Column(Integer)
    state = Column(Integer)

    failures = relationship('Failure', backref='check')
    measurements = relationship('Measurement', backref='check')

    def __init__(self, test, control):
        self.test = test
        self.control = control

        self.result = 'Pending'
        self.failures = []

    def eval_value(self, value, characteristic, uncertainty=None):
        if hasattr(obj, name)
        if hasattr(characteristic, 'limits'):
            limits = characteristic.limits
        if type(limits[0]) != list:
            if limits[1] is not None:
                if value > limits[1]:
                    self.failures.append(Failure('high', characteristic))
            if limits[0] is not None:
                if value < limits[0]:
                    self.failures.append(Failure('low', characteristic))



    def report_failure(self, failure):
        self.failures.append(failure)
        self.result = 'NOK'

    def execute(**kwargs):
        pass


class DoDAO:
    """Class to operate with Do Objects"""
    pass
