from tests.domain import OnMemoryDataTest
from quactrl.managers.crud import Crud
from quactrl.domain.nodes import Person


class A_Crud(OnMemoryDataTest):
    def setup_method(self, method):
        super().setup_method(method)
        self.manager = Crud()

    def _create_bond(self):
        person = Person(key='007', description='Bond, James')
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

    def should_update_domain_object(self):
        id = self._create_bond()

        self.manager.update('person', id, description='Ruiz, Salvador')

        person = self.session.query(Person).filter_by(id=id).one()
        assert person.description == 'Ruiz, Salvador'

    def should_remove_domain_object(self):
        id = self._create_bond()

        self.manager.delete('person', id)

        res = self.dal.Session().query(Person).filter_by(id=id).one_or_none()
        assert res is None