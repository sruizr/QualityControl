import quactrl.domain.items as i
import quactrl.domain.resources as r
from tests import TestWithPatches
from tests.domain import EmptyDataTest
from unittest.mock import Mock


class A_Part(EmptyDataTest):
    def setup_method(self, method):
        super().setup_method(method)
        self.part = i.Part()
        self.part.tracking = '1234'
        self.part_model = r.PartModel()
        self.part_model.key = 'partnumber'
        self.part.part_model = self.part_model
        self.characteristic = r.Characteristic()

    def should_start_with_part_model(self):
        self.session.add(self.part)
        self.session.commit()
        assert self.part.tracking == '1234'
        assert self.part.resource.key == 'partnumber'

    def should_store_measurements(self):
        measurement = i.Measurement(self.part, self.characteristic, 1.2)

        self.session.add(self.part)
        self.session.commit()

        assert self.part.measurements[0] == measurement

    def should_store_defects(self):
        pass


class A_Defect(EmptyDataTest):
    def setup_method(self, method):
        super().setup_method(method)
        self.part = i.Part()

        characteristic = r.Characteristic()
        self.failure_mode = r.FailureMode(characteristic, 'lw')

    def should_keep_part(self):

        defect = i.Defect(self.part, self.failure_mode)

        self.session.add(defect)
        self.session.commit()

        assert defect.part == self.part
        assert self.part.defects[0] == defect

    def should_have_only_one_part_linked(self):
        other_part = i.Part()
        other_part.tracking = '4321'

        defect = i.Defect(self.part, self.failure_mode)
        self.session.add(defect)
        self.session.commit()

        defect.part = other_part
        self.session.commit()

        assert defect.part == other_part
        assert not self.part.defects
        assert other_part.defects[0] == defect


class A_Measurement(EmptyDataTest):

    def setup_method(self, method):
        super().setup_method(method)
        self.part = i.Part()

        self.characteristic = r.Characteristic()

    def should_keep_part(self):
        measurement = i.Measurement(self.part, self.characteristic, 1.0)

        self.session.add(measurement)
        self.session.commit()

        assert measurement.part == self.part
        assert self.part.measurements[0] == measurement


    def should_have_only_one_part_linked(self):
        other_part = i.Part()

        measurement = i.Measurement(self.part, self.characteristic, value=1.0)
        self.session.add(measurement)
        self.session.commit()

        measurement.part = other_part
        self.session.commit()

        assert measurement.part == other_part
        assert not self.part.measurements
        assert other_part.measurements[0] == measurement

    def should_have_only_one_defect_linked(self):
        failure_mode = r.FailureMode(self.characteristic, 'lw')
        other_failure_mode = r.FailureMode(self.characteristic, 'slw')

        defect = i.Defect(self.part, failure_mode)
        other_defect = i.Defect(self.part, other_failure_mode)

        measurement = i.Measurement(self.part, self.characteristic, value=1.0)
        measurement.defect = defect
        self.session.add(measurement)
        self.session.commit()

        assert defect.measurements[0] == measurement

        measurement.defect = other_defect
        self.session.commit()

        assert measurement.defect == other_defect
        assert other_defect.measurements[0] == measurement
        assert len(defect.measurements) == 0

    def should_eval_ok_from_limits(self):
        characteristic = r.Characteristic()
        characteristic.key = 'char'
        part = i.Part()
        part.tracking = 'tr'

        measurement = i.Measurement(part, characteristic, 2.0)
        defect = measurement.evaluate([None, None], 1.0)
        assert defect is None

        # hi failure_mode
        defect = measurement.evaluate([-0.5, 0.5], 0.0)
        assert defect.failure_mode.key == 'hi-char'
        assert defect.tracking == 'tr*hi-char'
        assert part.defects[0] == defect

        # lw failure_mode
        defect = measurement.evaluate([2.1, 3.0], 0.0)
        assert defect.failure_mode.key == 'lw-char'
        assert defect.tracking == 'tr*lw-char'
        assert part.defects[1] == defect

        # shi failure_mode
        defect = measurement.evaluate([-2.5, 2.5], 0.6)
        assert defect.failure_mode.key == 'shi-char'
        assert defect.tracking == 'tr*shi-char'
        assert part.defects[2] == defect

        # lw failure_mode
        defect = measurement.evaluate([1.5, 3.0], 0.6)
        assert defect.failure_mode.key == 'slw-char'
        assert defect.tracking == 'tr*slw-char'
        assert part.defects[3] == defect


class A_Document(EmptyDataTest):

    def should_report_from_test(self):
        pass
