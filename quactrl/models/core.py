import datetime
"""Base of model layer is a graph
"""

class NotFoundQuantity(Exception):
    pass


class Node:
    pass


class Resource:
    pass


class ResourceLink:
    pass


class Item:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.flow_qty = 0
        self.tokens = []

    @property
    def qty(self):
        return sum([token.qty for token in self.tokens])

    @property
    def stocks(self):
        stocks = {}
        for token in self.tokes:
            if token.node not in stocks:
                stocks[token.node] = 0
            stocks[token.node] += token.qty

        return {node: qty
                for node, qty in stocks.items()
                if qty != 0}

    def add(self, qty, node, flow=None):
        """Add a qty on a node
        """
        self.tokens.append(
            Token(self, node, qty, flow)
        )

    def remove(self, qty, node, flow):
        """Remove a qty of item on node
        """
        stocks = self.stocks
        if node in stocks:
            if qty >= stocks[node]:
                self.tokens.append(
                    Token(self, node, -qty, flow)
                )
            else:
                raise NotFoundQuantity()
        else:
            raise NotFoundQuantity()

    def clear(self, flow, node=None):
        """Removes all quantities from node
        """
        qty = self.stocks.get(node)
        if qty:
            self.remove(qty, node, flow)

    def move(self, from_node, to_node, flow, qty=None):
        avalaible_qty = self.stocks.get(from_node)
        if not qty:
            qty = avalaible_qty

        if qty > avalaible_qty:
            raise NotFoundQuantity()

        self.remove(qty, from_node, flow)
        self.add(qty, to_node, flow)

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


class UnitaryItem(Item):
    """Item which has only 1 unit as qty
    """
    def add(self, node, flow=None):
        if self.stocks:
            raise Exception('Unitary item can not add more quantity to any node')
        super().add(1, node, flow)

    def remove(self, node, flow):
        super().remove(1, node, flow)

    def move(self, from_node, to_node, flow):
        super().move(from_node, to_node, flow, 1)


class ItemLink:
    pass


class Path:
    pass


class Flow:
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
    pass
