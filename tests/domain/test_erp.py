from quactrl.domain.erp import (
    Resource, ResourceRelation, Node, NodeRelation, Item, ItemRelation
    )
from quactrl.domain.data import DataAccessLayer
from tests import DataTest


def setup_module(module):
    global dal
    dal = DataAccessLayer()
    dal.db_init('sqlite:///:memory:', False)
    dal.prepare_db()


class A_Node(DataTest):
    def setup_method(self, method):
        self._transaction = dal.connection.begin_nested()
        self.session = dal.Session()

    def teardown_method(self, method):
        # self.session.rollback()
        self.session.close()
        self._transaction.rollback()

    def should_be_created_node(self):

        session = dal.Session()
        node = Node('key', 'description')
        session.add(node)

        assert node.id is None
        session.commit()

        assert node.id == 1
        assert node.is_a is None


class A_RelationNode:
    def setup_method(self, method):
        self._transaction = dal.connection.begin_nested()
        self.session = dal.Session()

    def teardown_method(self, method):
        # self.session.rollback()
        self.session.close()
        self._transaction.rollback()

    def should_keep_destinations_on_node(self):
        session = dal.Session()

        from_node = Node(key='from_node')
        to_node = Node(key='to_node')
        relation = NodeRelation(from_node, to_node)

        session.add(from_node)
        session.add(to_node)
        session.add(relation)
        # bulk_save_objects(
        #     [from_node, to_node]
        #     )
        session.commit()

        assert from_node.destinations[0].to_node == to_node
        assert relation.qty == 1.0
        assert relation.relation_class == 'contains'
        assert from_node.id is not None
        assert to_node.id is not None

class A_Item:
    def should_be_created(self):
        resource = Resource()

        session = dal.Session()

        item = Item(resource)
        session.add(item)

        session.commit()

        assert item.id is not None
        assert item.is_a is None
        assert item.tracking == ''
        assert item.state == 'active'


class A_ItemRelation:
    def should_keep_destinations_on_items(self):
        pass
