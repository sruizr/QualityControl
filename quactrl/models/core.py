import datetime
from quactrl.helpers import get_function
"""Base of model layer is a graph
"""

class NotFoundQuantity(Exception):
    pass


class Node:
    def __init__(self, **kwargs):
        for att, value in kwargs.items():
            setattr(self, att, value)


class Resource:
    pass


class Item:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.flow_qty = 0
        self.tokens = []

    @property
    def qty(self):
        return sum([token.qty
                    for token in self.tokens
                    if token.current])

    @property
    def stocks(self):
        stocks = {}
        for token in self.tokens:
            if token.current:
                stocks[token.node] = token.qty

        return stocks

    def get_token(self, node):
        for token in self.tokens:
            if token.current and token.node == node:
                return token

    def update_qty(self, qty, node, flow):
        """Add a qty on a node
        """
        if qty == 0:
            self.clear(node, flow)
        elif qty < 0:
            raise Exception('Quantity should not be negative')
        else:
            token = self.get_token(node)
            if token:
                token.current = False

            new_token = Token(self, node, qty, flow)
            self.tokens.append(new_token)

    def clear(self, node, flow):
        """Empty node from quantity
        """
        token = self.get_token(node)
        if token:
            token.current = False
        new_token = Token(self, node, 0, flow)
        token.current = False
        self.tokens.append(token)

    def move(self, from_node, to_node, flow, qty=None):
        token = self.get_token(from_node)
        if qty is None:
            qty = token.qty

        self.update_qty(token.qty - qty, from_node, flow)
        self.update_qty(qty, to_node, flow)

    def undo_flow(self, flow):
        "Clear all tokens of a flow"
        for token in self.tokens:
            if token.flow == flow:
                self.tokens.pop(token)


class Token:
    def __init__(self, item, node, qty, flow):
        self.item = item
        self.node = node
        self.qty = qty
        self.flow = flow
        self.current = True


class UnitaryItem(Item):
    """Item which has only 1 unit as qty
    """
    def add(self, node, flow=None):
        if self.stocks:
            raise Exception('Unitary item can not add more quantity to any node')
        super().update_qty(1, node, flow)

    def remove(self, node, flow):
        super().clear(node, flow)

    def move(self, from_node, to_node, flow):
        super().move(from_node, to_node, flow, 1)


class Path:
    @property
    def method(self):
        if not hasattr(self, '_method'):
            self._method = get_function(self.method_name) if self.method_name else None
        return self._method


class Flow:
    def __init__(self, responsible, update=None, **kwargs):
        self.responsible = responsible
        self.update = update
        for att, value in kwargs.items():
            setattr(self, att, value)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state
        if hasattr(self, 'update'):
            self.update(state, self)

    def start(self):
        self.state = 'started'
        self.started_on = datetime.datetime.now()

    def close(self):
        self.state = 'closed'
        self.finished_on = datetime.datetime.now()
