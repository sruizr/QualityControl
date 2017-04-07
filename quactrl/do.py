from quactrl import (
                     Column, ForeignKey, relationship, Model
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
    def __init__(self, test_operation, sample, operator):
        self.detection_point


    def begin_test():
        pass


class Check(Model):
    __tablename__ = 'checks'
    control = Column(Integer)
    failures = relationship('dnfas')
    result = Column(Integer)
    sampling = Column()

    def __init__(self, control, sampling):
        self.control = control
        self.failures = []
        self.result = 'Pending'
        self.sampling = sampling

    def report_failure(self, failure):
        self.failures.append(failure)
        self.result = 'NOK'

    def end_check(self):
        if not self.failures:
            self.result = 'OK'


class DoDAO:
    """Class to operate with Do Objects"""
    pass
