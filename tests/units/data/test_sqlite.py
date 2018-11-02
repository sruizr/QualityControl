from unittest.mock import Mock
import datetime
from quactrl.data.sqlite import TestSaver


class A_TestSaver:
    def setup_method(self, method):
        test = Mock()
        test._id = 0
        test.started_on = datetime.datetime.now()
        test.finished_on = None
        test.responsible.key = 'sruiz'
        test.state = 'success'


        part = test.part
        part.serial_number = '1234567890'
        part.model.key = 'part_number'
        part._id = 0

        check = Mock()
        check.__class__.__name__ = 'Check'
        check._id = 0
        check.test = test
        check.started_on = datetime.datetime.now()
        check.finished_on = datetime.datetime.now()
        check.requirement.description =  'requirement'
        check.state = 'ok'
        check.measurements = []
        check.defects = []

        measurement = Mock()
        measurement.characteristic.key = 'char'
        measurement.tracking = '22222'
        measurement.value = 1.0
        check.measurements.append(measurement)

        defect = Mock()
        defect.failure.key = 'fa'
        defect.tracking = '112123'
        check.defects.append(defect)


        action = Mock()
        action.test = test
        action.started_on = datetime.datetime.now()
        action.finished_on = datetime.datetime.now()
        action.state = 'done'
        action.step.method_name = 'method'

        test.actions = []
        test.actions.append(check)
        test.actions.append(action)

        self.test = test

    def should_create_schema(self):
        test_saver = TestSaver(':memory:')
        test_saver.c.execute('SELECT * FROM Parts')
        test_saver.c.execute('SELECT * FROM Tests')
        test_saver.c.execute('SELECT * FROM Actions')
        test_saver.c.execute('SELECT * FROM Measurements')
        test_saver.c.execute('SELECT * FROM Defects')

    def should_upsert_part(self):
        test_saver = TestSaver(':memory:')

        part = self.test.part

        test_saver.upsert_part(part)
        assert part._id == 1

        part._id = None
        test_saver.upsert_part(part)

        assert part._id == 1

    def should_insert_test(self):
        test_saver = TestSaver()
        test_saver.insert_test(self.test)

        assert self.test._id == 1


    def should_insert_check(self):
        test_saver = TestSaver()
        check = self.test.actions[0]
        test_saver.insert_check(check)

        assert check._id == 1

    def should_insert_action(self):
        test_saver = TestSaver()
        action = self.test.actions[1]

        test_saver.insert_action(action)
        assert action._id == 1

    def should_insert_measurement(self):
        test_saver = TestSaver()
        measurement = self.test.actions[0].measurements[0]

        test_saver.insert_measurement(measurement, self.test.actions[0])
        assert measurement._id == 1

    def should_insert_defect(self):
        test_saver = TestSaver()
        defect = self.test.actions[0].defects[0]

        test_saver.insert_defect(defect, self.test.actions[0])
        assert defect._id == 1

    def should_save(self):
        test_saver = TestSaver()
        test_saver.save(self.test)

        assert self.test._id == 1
        assert self.test.actions[0]._id == 1
        assert self.test.actions[1]._id == 2
        check = self.test.actions[0]
        assert check.measurements[0]._id == 1
        assert check.defects[0]._id == 1

    def should_clear(self):
        test_saver = TestSaver()
        test_saver.save(self.test)
