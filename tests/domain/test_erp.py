from quactrl.domain.base import (
    Resource, ResourceRelation, Node, NodeRelation, Item, ItemRelation,
    Path, PathResource, Token, Flow, Pars
    )
from quactrl.domain.persistence import DataAccessLayer
from tests.domain.test_data import OnMemoryTest


class A_Node(OnMemoryTest):
    def should_be_created_node(self):
        node = Node('key', 'description')
        self.session.add(node)

        assert node.id is None
        self.session.commit()

        assert node.id is not None
        assert node.is_a is None


class A_RelationNode(OnMemoryTest):

    def should_keep_destinations_on_node(self):

        from_node = Node(key='from_node')
        to_node = Node(key='to_node')
        relation = NodeRelation(from_node, to_node)

        self.session.add(from_node)
        self.session.add(to_node)
        self.session.add(relation)
        self.session.commit()

        assert from_node.destinations[0].to_node == to_node
        assert relation.qty == 1.0
        assert relation.relation_class == 'contains'
        assert from_node.id is not None
        assert to_node.id is not None


class A_Item(OnMemoryTest):
    def should_be_created(self):
        resource = Resource('r_key')
        item = Item(resource)

        self.session.add(item)
        self.session.commit()

        assert item.id is not None
        assert item.is_a is None
        assert item.tracking == ''
        assert item.state == 'active'

    def should_have_optional_pars(self):
        resource = Resource('r_key')
        item = Item(resource)
        item.pars = Pars({'1': 2})

        self.session.add(item)
        self.session.commit()

        assert item.pars.get() == {'1': 2}


class A_ItemRelation(OnMemoryTest):
    def should_keep_destinations_on_items(self):
        resource = Resource('r_key')
        item = Item(resource)
        sub_item = Item(resource)

        rel = ItemRelation()
        rel.from_item = item
        rel.to_item = sub_item

        self.session.add(item)
        self.session.add(sub_item)
        self.session.commit()

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

        self.session.add_all(
            [from_node, to_node, parent, path]
            )
        self.session.commit()

        assert parent.children[0] == path
        assert parent.sequence == 0
        assert parent.method_name == ''

    def _should_insert_items(self):
        pass

    def _should_close(self):
        pass

    def _should_add_resource(self):
        pass

    def _should_add_step(self):
        pass


class A_Resource(OnMemoryTest):
    def should_be_created(self):
        resource = Resource('key', 'description')
        self.session.add(resource)
        self.session.commit()

        assert resource.id is not None
        assert resource.pars is None

    def should_have_optional_pars(self):
        resource = Resource('key', 'description')
        resource.pars = Pars({'1': 1})
        self.session.add(resource)
        self.session.commit()

        assert resource.id is not None
        assert resource.pars.get() == {'1': 1}


class A_PathResource(OnMemoryTest):
    def should_add_resources_on_path(self):
        path = Path()
        resource = Resource('r_key')

        path.add_resource(resource=resource)
        self.session.add(path)
        self.session.commit()

        assert resource.id is not None
        assert path.resource_list[0].resource == resource


class A_Token(OnMemoryTest):

    def should_should_init(self):
        resource = Resource('r_key')
        item = Item(resource)
        node = Node('n_key')

        token = Token(node=node, item=item)

        self.session.add(token)
        self.session.commit()

        assert token.qty == 1.0
        assert token.flow is None
        assert token.item == item
        assert token.node == node


class A_Flow(OnMemoryTest):
    def should_init_from_path(self):
        path = Path()
        responsible = Node('person')

        flow = Flow(path, responsible)

        self.session.add(flow)
        self.session.commit()

        assert flow.id is not None
        assert flow.path == path
        assert flow.responsible == responsible
