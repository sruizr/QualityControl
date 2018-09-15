import quactrl.domain.resources as r
import quactrl.domain.base as b
from tests.domain import EmptyDataTest
import pytest


class A_IsARelation(EmptyDataTest):
    def should_stores_part_grouping(self):
        part_model = r.PartModel()
        part_group = r.Group()

        is_a = r.Clasification()
        is_a.group = part_group
        is_a.member = part_model
        self.session.add(is_a)
        self.session.commit()

        assert part_model.groups[0].group == part_group
        assert part_group.members[0].member == part_model


class A_CompositionRelation(EmptyDataTest):
    def should_stores_part_compositions(self):
        part = r.PartModel()
        component = r.PartModel()

        composition = r.Composition()
        composition.component = component
        composition.system = part
        self.session.add(composition)
        self.session.commit()

        assert composition.qty == 1.0
        assert part.components[0].component == component


class A_Requirement(EmptyDataTest):
    def should_stores_requirements_for_part(self):
        part = r.PartModel()
        char = r.Characteristic()

        requirement = r.Requirement()
        requirement.characteristic = char
        requirement.from_resource = part
        requirement.pars = b.Pars()
        requirement.pars.dict = {'limits': [1, 2]}
        self.session.add(requirement)
        self.session.commit()

        assert part.requirements[0].characteristic == char
        assert part.requirements[0].pars['limits'] == [1, 2]

    def should_stores_requirements_for_characteristic(self):
        main = r.Characteristic()
        char = r.Characteristic()

        requirement = r.Requirement()
        requirement.characteristic = char
        requirement.from_resource = main
        requirement.pars = b.Pars()
        requirement.pars.dict = {'limits': [1, 2]}
        self.session.add(requirement)
        self.session.commit()

        assert main.requirements[0].characteristic == char
        assert main.requirements[0].pars['limits'] == [1, 2]

    def should_stores_requirements_for_part_group(self):
        group = r.Characteristic()
        char = r.Characteristic()

        requirement = r.Requirement()
        requirement.characteristic = char
        requirement.from_resource = group
        requirement.pars = b.Pars()
        requirement.pars.dict = {'limits': [1, 2]}

        self.session.add(requirement)
        self.session.commit()

        assert group.requirements[0].characteristic == char
        assert group.requirements[0].pars['limits'] == [1, 2]


class A_Failure(EmptyDataTest):
    def _should_stores_failure_modes_from_characteristic(self):
        char = r.Characteristic()

        failure = r.Failure(char, 'lw')
        self.session.add(failure)
        self.session.commit()

        assert char.failures[0] == failure

    def should_avoid_repeat_failure_modes(self):
        char = r.Characteristic()

        failure = r.Failure(char, 'lw')
        self.session.add(failure)
        self.session.commit()

        try:
            r.Failure(char, 'lw')
            pytest.fail('DuplicatedFailure exception should be raised')
        except r.DuplicatedFailure:
            pass
