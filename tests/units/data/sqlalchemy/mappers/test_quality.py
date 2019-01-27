from . import TestMapper
from quactrl.data.sqlalchemy.mappers import core, products, quality # operations, quality
import quactrl.models.products as prd
import quactrl.models.quality as qua


class A_QualityMapper(TestMapper):
    def should_link_defects_and_measurements_to_subject(self):
        model = prd.PartModel('model')

        subject = qua.Subject(resource=model, tracking='1234')

        element = prd.Element('e')
        attribute = prd.Attribute('a')
        characteristic = prd.Characteristic(attribute, element)
        mode = qua.Mode('m')
        characteristic.add_failure_mode(mode)

        subject.get_defect(characteristic.failure_modes['m'])
        subject.get_measurement(characteristic)

        session = self.Session()
        session.add(subject)
        session.commit()

        session = self.Session()
        subject = session.query(qua.Subject).first()

        assert subject.defects[0].tracking == '1234/m-a@e'
        assert subject.measurements[0].tracking == '1234/a@e'
