from . import TestMapper
from quactrl.data.sqlalchemy.mappers import core, products, quality
import quactrl.models.products as prd


class A_ProductModule(TestMapper):
    def should_link_part_models_and_groups(self):
        session = self.Session()

        part_group = prd.PartGroup('group_key', 'group_name', 'group_description', {'par': 1})
        session.add(part_group)

        part_model = prd.PartModel('model_key', 'model_name', 'model_description', {'model': 'par'})
        session.add(part_model)

        part_model.add_group(part_group)

        session.commit()

        other_session = self.Session()

        part_group = other_session.query(prd.PartGroup).first()
        assert part_group.models[0].key == 'model_key'

    def should_link_requirements_with_others(self):
        session = self.Session()

        element = prd.Element('e', 'el')
        attribute = prd.Attribute('a', 'att')
        characteristic = prd.Characteristic(attribute, element)
        requirement = prd.Requirement(characteristic, 'req_key', specs={'limits': [1,2]})
        sub_req = prd.Requirement(characteristic, 'sub_key', specs={'max_abs': 1 })

        requirement.add_requi(sub_req)

        session.add(requirement)
        session.commit()

        session = self.Session()

        req = session.query(prd.Requirement).first()
        req.requirements['sub_key'].specs['max_abs'] == 1
