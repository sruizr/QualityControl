from tests.domain import EmptyDataTest
from quactrl.managers.crud import Crud
import quactrl.domain.nodes as n


class A_Crud(EmptyDataTest):
    def setup_method(self, method):
        super().setup_method(method)
        self.manager = Crud()

    def _create_bond(self):
        person = n.Person(key='007', description='Bond, James')
        self.session.add(person)
        self.session.commit()
        id = person.id
        assert type(id) is int
        return id

    def should_create_domain_object(self):
        person = self.manager.create('person', key='007', description='Bond, James')
        assert type(person.id) is int

    def should_retrieve_domain_object(self):
        self._create_bond()

        person = self.manager.read('person', key='007')
        assert person.description == 'Bond, James'

    def should_update_domain_object_fields(self):
        id = self._create_bond()

        self.manager.update('person', id, description='Ruiz, Salvador')

        person = self.session.query(n.Person).filter_by(id=id).one()
        assert person.description == 'Ruiz, Salvador'

    def should_update_domain_object_assotiations_by_keys(self):
        id = self._create_bond()

        role = n.Role(key='admin')
        self.session.add(role)
        self.session.commit()

        self.manager.update('person', id, roles=['admin'])
        person = self.session.query(n.Person).filter_by(id=id).one()
        assert person.roles[0] == role

    def should_update_domain_object_assotiations_by_ids(self):
        id = self._create_bond()

        role = n.Role(key='admin')
        self.session.add(role)
        self.session.commit()

        self.manager.update('person', id, roles=[role.id])
        person = self.session.query(n.Person).filter_by(id=id).one()
        assert person.roles[0] == role


    def should_remove_domain_object(self):
        id = self._create_bond()

        self.manager.delete('person', id)

        res = self.dal.Session().query(n.Person).filter_by(id=id).one_or_none()
        assert res is None

    def should_insert_person(self):

        person = self.manager.create('person', **{'key': '007', 'name':'bond', 'description': 'Bond, James'})

        stored_person = self.session.query(n.Person).filter(n.Person.key=='007').one_or_none()

        assert stored_person == person
        assert person.id

    def should_create_domain_object_with_pars(self):
        self.manager.create('person', **{'key': '007', 'pars': {'password':'licence to kill'}})

        stored_person = self.session.query(n.Person).filter(n.Person.key=='007').one_or_none()

        assert stored_person.pars['password'] == 'licence to kill'
