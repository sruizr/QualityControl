import quactrl.domain.items as i
import quactrl.domain.resources as r
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
    def should_keep_part(self):
        pass


class A_Measurement(EmptyDataTest):
    pass


class A_Document(EmptyDataTest):
    pass
