import quactrl.domain.nodes as n
from tests.domain import EmptyDataTest


class A_Person(EmptyDataTest):
    def should_have_roles(self):
        role_1 = n.Role('role_1')
        role_2 = n.Role('role_2')

        person = n.Person('person')

        person.roles.append(role_1)
        person.roles.append(role_2)
        import pdb; pdb.set_trace()

        self.session.add(person)
        self.session.commit()


        assert role_1.members[0] == person
