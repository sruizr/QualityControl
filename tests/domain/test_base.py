from tests.domain import EmptyDataTest
import json
import quactrl.domain.base as base
import pytest


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
    def should_be_created_from_path_definition(self):
        pass


class An_Item(EmptyDataTest):
    def setup_method(self, method):
        super().setup_method(method)
        resource = base.Resource(key='resource_key')
        self.item = base.Item(resource, tracking='123456789')

    def should_produce_tokens(self):
        flow = base.Flow()

        flow.destination = base.Node(key='destination')
        flow.origin = base.Node(key='origin')

        self.item.produce(flow, 2)

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
        self.item.produce(flow, 3)

        assert self.item.avalaible_tokens[0].qty == 3
        # 3 units on node_1
        self.session.add(self.item)
        self.session.commit()

        next_flow = base.Flow()
        next_flow.origin = flow.destination
        self.item.consume(next_flow, 1)
        self.session.commit()

        assert len(self.item.avalaible_tokens) == 1
        assert self.item.avalaible_tokens[0].qty == 2

        self.item.consume(next_flow)
        self.session.commit()
        assert len(self.item.avalaible_tokens) == 0

    def should_consume_subitems(self):
        pass

    def should_get_stocks(self):
        flow_1 = base.Flow()
        flow_1.destination = node_0 = base.Node(key='node_0')
        flow_2 = base.Flow()
        flow_2.destination = node_1 = base.Node(key='node_1')

        self.item.produce(flow_1, 1)
        self.item.produce(flow_2, 2)
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

    def should_have_compsution_plan(self):
        pass

    def should_have_production_plan(self):
        pass

    def should_confirm_if_can_consume_resource(self):
        pass

    def should_confirm_if_can_produce_resource(self):
        pass

    def should_confirm_if_responsible_can_execute_path(self):
        pass
