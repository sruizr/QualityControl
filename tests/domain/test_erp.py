from quactrl.domain.erp import (
    Resource, ResourceRelation, Node, NodeRelation
    )
from quactrl.domain.data import DataAccessLayer


def setup_module(module):
    global dal
    dal = DataAccessLayer()
    dal.db_init('sqlite:///:memory:', False)
    dal.prepare_db()


class A_Node:
    def should_open_node(self):

        session = dal.Session()

        node = Node()
        node.description = 'description'
        node.key = 'key'

        other_node = Node()
        other_node.description = 'other description'
        other_node.key = 'o_key'

        rel = NodeRelation()
        rel.from_node = node
        rel.to_node = other_node

        session.add(node)
        session.add(other_node)
        session.add(rel)

        assert node.id is None
        session.commit()

        assert node.id is not None
        assert node.is_a is None

        assert node.destinations[0].to_node == other_node
