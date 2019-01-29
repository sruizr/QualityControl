from . import TestMapper
from quactrl.data.sqlalchemy.mappers import core, products, operations, quality
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
        requirement = prd.Requirement(characteristic, 'a@e>A', specs={'limits': 1})

        subject.get_measurement(requirement)
        subject.get_defect(requirement, 'm')

        session = self.Session()
        session.add(subject)
        session.add(subject)
        session.commit()

        session = self.Session()
        subject = session.query(qua.Subject).first()

        assert subject.defects[0].tracking == '1234/m-a@e>A'
        assert subject.measurements[0].tracking == '1234/a@e>A'

        assert subject.measurements[0].subject == subject
