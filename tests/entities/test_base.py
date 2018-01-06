import quactrl.entities.base as base
from quactrl.entities import DataAccessLayer


dal = DataAccessLayer()


class A_DataAccessLayer:

    def should_have_a_test(self):
        dal.db_init('sqlite:///:memory:', True)
        dal.prepare_db()

        session = dal.Session()

        node = base.Node()
        node.description = 'description'
        node.key = 'key'
        node.name = 'name'
        node.parameters = '{"test": 1}'
        node.role = 'quactrl.Class'

        session.add(node)

        assert node.id is None
        session.commit()

        assert node.id is not None
        assert node.is_
