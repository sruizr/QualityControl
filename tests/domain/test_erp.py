from quactrl.domain.erp import (
    Resource, ResourceRelation, Node, NodeRelation, Item, ItemRelation,
    Path, PathResource, Movement
    )
from quactrl.domain.data import DataAccessLayer
from tests.domain.test_data import OnMemoryTest


class A_Node(OnMemoryTest):
    def should_be_created_node(self):

        session = self.dal.Session()
        node = Node('key', 'description')
        session.add(node)

        assert node.id is None
        session.commit()

        assert node.id is not None
        assert node.is_a is None


class A_RelationNode(OnMemoryTest):

    def should_keep_destinations_on_node(self):
        session = self.dal.Session()

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


class A_Item(OnMemoryTest):
    def should_be_created(self):
        resource = Resource()
        item = Item(resource)

        session = self.dal.Session()
        session.add(item)
        session.commit()

        assert item.id is not None
        assert item.is_a is None
        assert item.tracking == ''
        assert item.state == 'active'


class A_ItemRelation(OnMemoryTest):
    def should_keep_destinations_on_items(self):
        resource = Resource()
        item = Item(resource)
        sub_item = Item(resource)

        rel = ItemRelation()
        rel.from_item = item
        rel.to_item = sub_item

        session = self.dal.Session()
        session.add(item)
        session.add(sub_item)
        session.commit()

        assert item.destinations[0].to_item == sub_item
        assert item.destinations[0].relation_class == 'has'
        assert item.destinations[0].qty == 1.0
        assert rel.id is not None


class A_Path(OnMemoryTest):
    def should_be_created(self):
        from_node = Node('from_key')
        to_node = Node('to_key')

        parent = Path()
        path = Path()
        path.from_node = from_node
        path.to_node = to_node
        path.parent = parent

        session = self.dal.Session()
        session.add_all(
            [from_node, to_node, parent, path]
            )
        session.commit()

        assert parent.children[0] == path
        assert parent.sequence == 0
        assert parent.method_name == 'move'


class A_PathResource(OnMemoryTest):
    def should_keep_resources_on_path(self):
        path = Path()
        resource = Resource()
        path.resource_links.append(PathResource(resource=resource))

        session = self.dal.Session()
        session.add(path)

        session.commit()

        assert resource.id is not None
        assert path.resource_links[0].resource == resource


class A_Movement(OnMemoryTest):

    def should_record_movement_of_items(self):
        resource = Resource()
        item = Item(resource)
        from_node = Node('origin')

        movement = Movement(from_node=from_node, item=item)

        session = self.dal.Session()
        session.add(movement)
        session.commit()

        assert movement.qty == 1.0
        assert movement.user is None
