import quactrl.domain.items as i
import quactrl.domain.resources as r
from tests import TestWithPatches
from tests.domain import EmptyDataTest


class A_Part(EmptyDataTest):
    def setup_method(self, method):
        super().setup_method(method)
        part_model = r.PartModel(key='partnumber')
        self.part = i.Part(part_model, tracking='1234')
        self.characteristic = r.Characteristic('char')

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
        self.part_model = r.PartModel(key='partnumber')
        self.part = i.Part(self.part_model, tracking='1234')

        characteristic = r.Characteristic('char')
        self.failure_mode = r.FailureMode(characteristic, 'lw')

    def should_keep_part(self):

        defect = i.Defect(self.part, self.failure_mode)

        self.session.add(defect)
        self.session.commit()

        assert defect.part == self.part
        assert self.part.defects[0] == defect

    def should_have_only_one_part_linked(self):
        other_part = i.Part(self.part_model, tracking='4321')

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
        self.part_model = r.PartModel(key='partnumber')
        self.part = i.Part(self.part_model, tracking='1234')

        self.characteristic = r.Characteristic('char')

    def should_keep_part(self):
        measurement = i.Measurement(self.part, self.characteristic, 1.0)

        self.session.add(measurement)
        self.session.commit()

        assert measurement.part == self.part
        assert self.part.measurements[0] == measurement


    def should_have_only_one_part_linked(self):
        other_part = i.Part(self.part_model, tracking='4321')

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
        defect = i.Defect(self.part, failure_mode)

        measurement = i.Measurement(self.part, self.characteristic, value=1.0)
        self.session.add(measurement)
        self.session.commit()


        measurement.part = other_part
        self.session.commit()


        assert measurement.part == other_part
        assert not self.part.measurements
        assert other_part.measurements[0] == measurement

class A_Measurement_(TestWithPatchs):
    pass


class A_Document(EmptyDataTest):
    pass
