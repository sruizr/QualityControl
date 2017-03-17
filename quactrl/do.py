class Batch:
    def __init__(self, part_number, batch_number, operator):
        self.part_number = part_number
        self.batch_number = batch_number
        self.operator = operator
        self.close_date = None
        self.items = {}


class Item:
    def __init__(self, serial_number):
        self.sn = serial_number
        self.status = None
        self.tests = []

    def validate(self, serial_number):
        pass

    @classmethod
    def has_passed_test(self, serial_number):
        return False


class Check:
    def __init__(self, control, item):
        self.control = control
        self.failures = []
        self.result = 'Pending'
        self.item = item

    def report_failure(self, failure):
        self.failures.append(failure)
        self.result = 'NOK'

    def end_check(self):
        if not self.failures:
            self.result = 'OK'


class DoDAO:
    """Class to operate with Do Objects"""
    pass
