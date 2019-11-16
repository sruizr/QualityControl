from . import TestMapper
from quactrl.data.sqlalchemy.mappers import core, products, quality
import quactrl.models.products as prd
import quactrl.models.quality as qua


class A_ProductsMapper(TestMapper):
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
        part_groups = other_session.query(prd.PartGroup).all()
        assert len(part_groups) ==  1
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

        req = session.query(prd.Requirement).filter(prd.Requirement.key == 'req_key').first()
        req.requirements['sub_key'].specs['max_abs'] == 1


    def should_link_failure_modes_to_characteristics(self):
        session = self.Session()

        element = prd.Element('e_', 'el')
        attribute = prd.Attribute('a_', 'att')
        characteristic = prd.Characteristic(attribute, element)
        mode = qua.Mode('m', 'mode')
        characteristic.add_failure_mode(mode)

        session.add(characteristic)
        session.commit()

        other_session = self.Session()
        char = other_session.query(prd.Characteristic).filter(
            prd.Characteristic.key == 'a_@e_'
        ).first()
        assert char.failure_modes['m']
