from tests.domain import EmptyDataTest
from tests import TestWithPatches
import json
import quactrl.domain.base as base
import pytest
from unittest.mock import Mock, patch


class A_ParsMixin(EmptyDataTest):
    def should_load_other_attributes_in_pars(self):
        resource = base.Resource(key='key', name='name', description='description', other=1)
        assert resource.pars['other'] == 1

        resource.pars['another'] = 'value'

        assert resource.pars['another'] == 'value'
        self.session.add(resource)
        self.session.commit()

        assert resource.pars._dict_pars == {'another': 'value', 'other': 1}

        other = self.session.query(base.Resource).filter_by(key='key').one()

        assert json.loads(resource.pars._pars)['other'] == 1

    def should_modify_pars_one_by_one(self):
        resource = base.Resource(key='key', name='name', description='description', other=1)
        assert resource.pars['other'] == 1

        resource.pars['other'] = 2

        assert resource.pars['other'] == 2
        assert json.loads(resource.pars._pars)['other'] == 2


class A_Flow(EmptyDataTest):
    def should_persist_basic_relationships(self):
        flow = base.Flow()
        flow.path = base.Path(role=base.Node(key='role'))

        flow.responsible = base.Node(key='responsible')
        op = base.Flow()
        flow.operations.append(op)
        self.session.add(flow)
        self.session.commit()

        assert op.parent == flow
        assert flow.path.role.key == 'role'
        assert flow.responsible.key == 'responsible'

    @patch('quactrl.domain.base.datetime')
    def should_start_(self, mock_datetime):
        dinamic_field = Mock()
        flow = base.Flow()

        flow.start(d_field=dinamic_field)


        assert flow.inputs == []
        assert flow.outputs == []
        assert flow.d_field == dinamic_field
        assert not flow.origin
        assert not flow.destination
        assert flow.state == 'started'
        mock_datetime.now.assert_called_with()
        assert flow.started_on == mock_datetime.now.return_value

        # path = Mock()
        # flow.path = path

        # flow.start()
        # assert flow.origin == path.from_node
        # assert flow.destination == path.to_node

    @patch('quactrl.domain.base.datetime')
    def should_finish_flow(self, mock_datetime):
        flow = base.Flow()
        flow.state = 'started'

        flow.finish()
        mock_datetime.now.assert_called_with()
        assert flow.finished_on == mock_datetime.now.return_value
        assert flow.state == 'finished'

        flow.state = 'ongoing'
        flow.finish()
        assert flow.state == 'finished'

        flow.state = 'other'
        flow.finish()
        assert flow.state == 'other'

    @patch('quactrl.domain.base.datetime')
    def should_cancel_flow(self, mock_datetime):
        flow = base.Flow()

        flow.cancel()

        assert flow.finished_on == mock_datetime.now.return_value
        mock_datetime.now.assert_called_with()
        assert flow.state == 'cancelled'

    def should_execute(self):
        flow = base.Flow()

        flow.execute()

        path = base.Path()
        path.method = Mock()
        flow.path = path
        flow.execute()
        path.method.assert_called_with(flow)

    def should_create_operations(self):
        path = base.Path()
        steps = [base.Path() for _ in range(3)]
        for step in steps:
            path.steps.append(step)
            step.create_flow = Mock()
            step.create_flow.return_value = base.Flow()
        flow = base.Flow(path=path)
        flow.responsible = base.Node(key='resp')

        calls = []
        for step, operation in zip(steps, flow.op_creator()):
            assert operation == step.create_flow.return_value
            step.create_flow.assert_called_with()
            assert operation.responsible == flow.responsible
            assert operation.parent == flow

    def should_runs(self):
        flow = base.Flow()
        flow.start = Mock()
        flow.op_creator = Mock()
        flow.op_creator.return_value = [Mock()]
        flow.execute = Mock()
        flow.finish = Mock()
        flow.close = Mock()
        field = Mock()

        flow.run(field=field)

        flow.start.assert_called_with(field=field)
        flow.op_creator.return_value[0].run.assert_called_with()
        flow.execute.assert_called_with()
        flow.finish.assert_called_with()
        flow.close.assert_called_with()

    def should_close(self):
        flow = base.Flow()
        flow.allocate = Mock()
        flow.throw = Mock()

        flow.finished_on = Mock()
        flow.close()

        flow.allocate.assert_called_with()
        flow.throw.assert_called_with()

    def should_throw_inputs_and_outputs(self):
        flow = base.Flow()
        operations = [base.Flow() for _ in range(3)]
        for op in operations:
            op.throw = Mock()
            flow.operations.append(op)

        destination = base.Node('destination')
        origin = base.Node('origin')

        resource = base.Resource(key='res')
        _input = base.Item(resource)
        _input.consume = Mock()
        output = base.Item(resource)
        output.produce = Mock()
        flow.origin = flow.destination = None
        flow.inputs = [_input]
        flow.outputs = [output]

        flow.throw()
        _input.consume.assert_not_called()
        output.produce.assert_not_called()
        for op in operations:
            op.throw.assert_called_with()

        flow.origin = origin
        flow.destination = destination

        flow.throw()
        _input.consume.asseert_called_with(flow)
        output.produce.assert_called_with(flow)

    def should_allocate_origin_and_destination(self):
        flow = base.Flow()
        operations = [base.Flow() for _ in range(3)]
        for op in operations:
            op.allocate = Mock()
            flow.operations.append(op)

        with pytest.raises(base.FlowAllocateException):
            flow.allocate()

        flow.finished_on = Mock()
        flow.state = 'finished'

        destination = base.Node('destination')
        origin = base.Node('origin')
        from_node = base.Node('from_node')
        to_node = base.Node('to_node')

        path = base.Path()
        path.from_node = from_node
        path.to_node = to_node

        flow.path = path

        flow.origin = origin
        flow.destination = destination
        flow.allocate()

        for op in operations:
            op.allocate.assert_called_with()

        assert flow.origin == origin
        assert flow.destination == destination

        flow.origin = flow.destination = None
        flow.allocate()

        assert flow.origin == from_node
        assert flow.destination == to_node

        parent_path = base.Path()
        parent_path.from_node = from_node
        parent_path.to_node = to_node
        path.parent = parent_path

        path.from_node = path.to_node = None
        flow.origin = flow.destination = None

        flow.allocate()
        assert flow.origin == from_node
        assert flow.destination == to_node

        flow.state = 'cancelled'
        flow.destination = destination
        flow.origin = origin

        flow.allocate()

        assert flow.destination == origin
        for op in operations:
            assert op.state == 'cancelled'


class An_Item(EmptyDataTest):
    def setup_method(self, method):
        super().setup_method(method)
        resource = base.Resource(key='resource_key')
        self.item = base.Item(resource, tracking='123456789')

    def should_produce_tokens(self):
        flow = base.Flow()
        flow.destination = base.Node(key='destination')
        flow.origin = base.Node(key='origin')

        self.item.qty = 2
        self.item.produce(flow)

        self.session.add(self.item)
        self.session.commit()

        other = self.session.query(base.Item).one()
        assert other.avalaible_tokens
        token = other.avalaible_tokens[0]
        assert token.qty == 2
        assert token.node == flow.destination
        assert token.consumer is None
        assert token.producer == flow

    def should_consume_tokens(self):
        flow = base.Flow()
        flow.origin = base.Node(key='node_0')
        flow.destination = base.Node(key='node_1')

        self.item.qty = 3
        self.item.produce(flow)

        assert self.item.avalaible_tokens[0].qty == 3
        # 3 units on node_1
        self.session.add(self.item)
        self.session.commit()

        next_flow = base.Flow()
        next_flow.origin = flow.destination
        self.item.qty = 1
        self.item.consume(next_flow)
        self.session.commit()

        assert len(self.item.avalaible_tokens) == 1
        assert self.item.avalaible_tokens[0].qty == 2
        self.item.qty = None
        self.item.consume(next_flow)
        self.session.commit()
        assert len(self.item.avalaible_tokens) == 0

    def should_get_stocks(self):
        flow_1 = base.Flow()
        flow_1.destination = node_0 = base.Node(key='node_0')

        flow_2 = base.Flow()
        flow_2.destination = node_1 = base.Node(key='node_1')

        self.item.qty = 1
        self.item.produce(flow_1)

        self.item.qty = 2
        self.item.produce(flow_2)
        self.session.commit()

        assert len(self.item.avalaible_tokens) == 2

        stocks = self.item.get_stocks()

        assert len(stocks) == 2
        assert node_0 in stocks
        assert node_1 in stocks
        assert stocks[node_1][0].qty + stocks[node_0][0].qty == 3


class A_Token(EmptyDataTest):
    def setup_method(self, method):
        super().setup_method(method)
        resource = base.Resource(key='resource')
        item = base.Item(resource, tracking='123456789')
        node = base.Node(key='node')
        flow = base.Flow()
        self.token = base.Token(item=item, node=node, qty=10, producer=flow )

    def should_split_when_consume_is_less_then_token_qty(self):
        flow = base.Flow()
        self.token.consume(flow, 5)
        self.session.commit()

        assert self.token.item.avalaible_tokens[0].qty == 5

    def should_consume_all_when_qty_is_none(self):
        flow = base.Flow()
        self.token.consume(flow)
        self.session.commit()

        assert len(self.token.item.avalaible_tokens)  == 0

    def should_raise_exception_when_qty_is_too_large(self):
        consumer = base.Flow()
        try:
            self.token.consume(consumer, 11)
            pytest.fail('StockException should be raised')
        except base.StockException:
            pass


class A_Path(EmptyDataTest):
    def setup_method(self, method):
        super().setup_method(method)
        self.path = base.Path()

    def should_persist_basic_relationships(self):
        path = self.path

        path.from_node = base.Node(key='from')
        path.to_node = base.Node(key='to')
        path.role = base.Node(key='role')

        self.session.add(path)
        self.session.commit()

        assert path.role.key == 'role'
        assert path.from_node.key == 'from'
        assert path.to_node.key == 'to'

    def should_contain_posible_resources(self):
        resource = base.Resource(key='resource')
        self.path.resources['out'] = resource

        self.session.add(self.path)
        self.session.commit()

        assert self.path.resources['out'] == resource

    def setup_validate_responsible(self):
        role = base.Node(key='role')
        self.path.role = role

    def should_validate_responsible(self):
        self.setup_validate_responsible()
        responsible = Mock()
        responsible.roles = [self.path.role]

        self.path.validate_responsible(responsible)

    def should_raise_responsible_exception_on_validate_responsible(self):
        self.setup_validate_responsible()
        responsible = Mock()
        responsible.roles = [Mock()]

        with pytest.raises(base.NotAuthorizedResponsible):
            self.path.validate_responsible(responsible)

    def setup_validate_item(self):
        resource = Mock()
        self.path.resources['out'] = resource

    def should_validate_item(self):
        self.setup_validate_item()
        item = Mock()
        item.resource = self.path.resources['out']

        self.path.validate_item(item)

        item = Mock()
        item.resource.groups = [self.path.resources['out']]
        self.path.validate_item(item)

    def should_raise_item_exception_on_validate_item(self):
        self.setup_validate_item()
        item = Mock()
        item.resource.groups = [Mock()]

        with pytest.raises(base.NoCompatibleItem):
            self.path.validate_item(item)

    def should_request_to_implement_create_flow(self):
        responsible = Mock()

        try:
            self.path.create_flow(responsible)
            pytest.fail('NotImplementedError should be raised')
        except NotImplementedError:
            pass

    def should_add_steps(self):
        path = base.Path()
        step = base.Path()
        path.steps.append(step)

        self.session.add(path)
        self.session.commit()

        assert step.parent == path
