from quactrl import (
    Column, ForeignKey, relationship, Model,
    dal, Integer, String, DATETIME, DECIMAL
)
import pdb



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

    def __init__(self, mode, characterisc, index=None):
        self.mode = mode
        self.characteristic = characterisc
        self.index = index

class Sample:
    pass


class Check(Model):
    __tablename__ = 'check'
    control = Column(Integer)
    test = Column(Integer)
    result = Column(Integer)
    state = Column(Integer)

    failures = relationship('Failure', backref='check')
    measuresss= relationship('Measurement', backref='check')

    def __init__(self, test, control):
        self.test = test
        self.control = control

        self.result = 'Pending'
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

        index = None
        for
        if type(limits[0]) != list:
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

    def execute(**kwargs):
        pass
