import quactrl.domain.resources as r
from tests.domain import EmptyDataTest
import pytest


class A_IsARelation(EmptyDataTest):
    def should_stores_part_grouping(self):
        part_model = r.PartModel(key='part')
        part_group = r.PartGroup(key='group_part')

        is_a = r.IsA(part_model, part_group)
        self.session.add(is_a)
        self.session.commit()

        assert part_model.groups[0].group == part_group
        assert part_group.members[0].member == part_model


class A_CompositionRelation(EmptyDataTest):
    def should_stores_part_compositions(self):
        part = r.PartModel(key='part')
        component = r.PartModel(key='component')

        composition = r.Composition(part, component)
        self.session.add(composition)
        self.session.commit()

        assert composition.qty == 1.0
        assert part.components[0].component == component


class A_Requirement(EmptyDataTest):
    def should_stores_requirements_for_part(self):
        part = r.PartModel(key='part')
        char = r.Characteristic(key='char')

        requirement = r.Requirement(part, char, {'limits': [1, 2]})
        self.session.add(requirement)
        self.session.commit()

        assert part.requirements[0].characteristic == char
        assert part.requirements[0].pars['limits'] == [1, 2]

    def should_stores_requirements_for_characteristic(self):
        main = r.Characteristic(key='main')
        char = r.Characteristic(key='char')

        requirement = r.Requirement(main, char, {'limits': [1, 2]})
        self.session.add(requirement)
        self.session.commit()

        assert main.requirements[0].characteristic == char
        assert main.requirements[0].pars['limits'] == [1, 2]

    def should_stores_requirements_for_part_group(self):
        group = r.Characteristic(key='group')
        char = r.Characteristic(key='char')

        requirement = r.Requirement(group, char, {'limits': [1, 2]})
        self.session.add(requirement)
        self.session.commit()

        assert group.requirements[0].characteristic == char
        assert group.requirements[0].pars['limits'] == [1, 2]


class A_Failure(EmptyDataTest):
    def _should_stores_failure_modes_from_characteristic(self):
        char = r.Characteristic(key='char')

        failure = r.Failure(char, 'low', 'lw')
        self.session.add(failure)
        self.session.commit()

        assert char.failures[0] == failure

    def should_avoid_repeat_failure_modes(self):
        char = r.Characteristic(key='char')

        failure = r.Failure(char, 'low', 'lw')
        self.session.add(failure)
        self.session.commit()

        try:
            r.Failure(char, 'olow', 'lw')
            pytest.fail('DuplicatedFailure exception should be raised')
        except r.DuplicatedFailure:
            pass
