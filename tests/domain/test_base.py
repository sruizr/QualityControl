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

        self.session.add(flow)
        self.session.commit()

        assert flow.path.role.key == 'role'
        assert flow.responsible.key == 'responsible'

    @patch('quactrl.domain.base.datetime')
    def should_prepare_flow(self, mock_datetime):
        flow = base.Flow()

        flow.prepare()

        assert flow.inputs == []
        assert flow.outputs == []
        assert not flow.origin
        assert not flow.destination
        assert flow.state == 'started'
        mock_datetime.now.assert_called_with()

        path = Mock()
        flow.path = path

        flow.prepare()
        assert flow.origin == path.from_node
        assert flow.destination == path.to_node

    @patch('quactrl.domain.base.datetime')
    def should_terminate_flow(self, mock_datetime):
        flow = base.Flow()

        _input = Mock()
        flow.inputs = [_input]
        output = Mock()
        flow.outputs = [output]
        flow.destination = Mock()
        flow.origin = Mock()

        flow.terminate()

        assert flow.finished_on == mock_datetime.now.return_value
        mock_datetime.now.assert_called_with()
        assert flow.state == 'finished'

        _input.consume.assert_called_with(flow)
        output.produce.assert_called_with(flow)

    @patch('quactrl.domain.base.datetime')
    def should_cancel_flow(self, mock_datetime):
        flow = base.Flow()

        _input = Mock()
        flow.inputs = [_input]
        output = Mock()
        flow.outputs = [output]
        flow.destination = Mock()
        flow.origin = origin = Mock()

        flow.cancel()

        assert flow.finished_on == mock_datetime.now.return_value
        mock_datetime.now.assert_called_with()
        assert flow.state == 'cancelled'
        assert origin == flow.destination

        _input.consume.assert_called_with(flow)
        output.produce.assert_called_with(flow)


class An_Item(EmptyDataTest):
    def setup_method(self, method):
        super().setup_method(method)
        resource = base.Resource(key='resource_key')
        self.item = base.Item(resource, tracking='123456789')

    def should_produce_tokens(self):
        flow = base.Flow()

        flow.destination = base.Node(key='destination')
        flow.origin = base.Node(key='origin')
        operation = base.Operation(flow)

        self.item.qty = 2
        self.item.op = operation
        self.item.produce()

        self.session.add(self.item)
        self.session.commit()

        other = self.session.query(base.Item).one()
        assert other.avalaible_tokens
        token = other.avalaible_tokens[0]
        assert token.qty == 2
        assert token.node == flow.destination
        assert token.consumer is None
        assert token.producer == operation

    def should_consume_tokens(self):
        flow = base.Flow()
        flow.origin = base.Node(key='node_0')
        flow.destination = base.Node(key='node_1')
        operation = base.Operation(flow)

        self.item.qty = 3
        self.item.op = operation
        self.item.produce()

        assert self.item.avalaible_tokens[0].qty == 3
        # 3 units on node_1
        self.session.add(self.item)
        self.session.commit()

        next_flow = base.Flow()
        next_flow.origin = flow.destination
        next_op = base.Operation(next_flow)
        self.item.qty = 1
        self.item.op = next_op
        self.item.consume()
        self.session.commit()

        assert len(self.item.avalaible_tokens) == 1
        assert self.item.avalaible_tokens[0].qty == 2
        self.item.qty = None
        self.item.consume()
        self.session.commit()
        assert len(self.item.avalaible_tokens) == 0


    def should_get_stocks(self):
        flow_1 = base.Flow()
        flow_1.destination = node_0 = base.Node(key='node_0')
        op_1 = base.Operation(flow_1)

        flow_2 = base.Flow()
        flow_2.destination = node_1 = base.Node(key='node_1')
        op_2 = base.Operation(flow_2)

        self.item.qty = 1
        self.item.op = op_1
        self.item.produce()

        self.item.qty = 2
        self.item.op = op_2
        self.item.produce()
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
        path.add_step(method='method.name')
        path.add_step(method='other.method.name')
        path.add_step(method='intermediate', sequence=3)

        self.session.add(path)
        self.session.commit()

        assert path.steps[0].sequence == 0
        assert path.steps[1].sequence == 3
        assert path.steps[2].sequence == 5
        assert path.steps[0].method_name == 'method.name'


class A_Step(EmptyDataTest):
    def should_persist_basic_relationships(self):
        path = base.Path()
        step = base.Step(path=path)

        self.session.add(step)
        self.session.commit()

        assert path.steps[0].sequence == 0


class A_Operation(EmptyDataTest, TestWithPatches):
    def setup_method(self, method):
        EmptyDataTest.setup_method(self, method)
        self.create_patches([
            'quactrl.domain.base.get_component',
            'quactrl.domain.base.datetime'
        ])

    def teardown_method(self, method):
        EmptyDataTest.teardown_method(self, method)
        TestWithPatches.teardown_method(self, method)

    def should_persist_basic_relationships(self):
        flow = base.Flow()
        step = base.Step(method_name='method.name', sequence=1)

        operation = base.Operation(flow, step)

        self.session.add(operation)
        self.session.commit()

        assert flow.operations[0] == operation
        assert operation.step == step
        assert operation.sequence == step.sequence
        self.patch['get_component'].assert_called_with('method.name')
        assert operation.method == self.patch['get_component'].return_value

    def should_start(self):
        step = base.Step()
        flow = base.Flow()

        operation = base.Operation(flow, step)
        operation.start()

        assert operation.started_on == self.patch['datetime'].now.return_value
        assert operation.state == 'started'

    def should_finish(self):
        step = base.Step()
        flow = base.Flow()

        operation = base.Operation(flow, step)
        operation.finish()

        assert operation.finished_on == self.patch['datetime'].now.return_value
        assert operation.state == 'done'

    def should_execute(self):
        step = base.Step()
        flow = base.Flow()

        operation = base.Operation(flow, step)
        operation.execute()

        self.patch['get_component'].return_value.assert_called_with(operation)
