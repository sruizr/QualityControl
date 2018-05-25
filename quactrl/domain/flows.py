1from sqlalchemy.orm import synonym, reconstructor
from quactrl.domain.base import (Resource, PathResource,
                                ItemRelation, Path, Node, Pars, Flow
                                 )
import quactrl.domain.items as items
import quactrl.domain.resources as resources
import quactrl.domain.queries as qry


class Create(Flow):
    """Special flow where a item/token is inserted into node"""
    def __init__(self, responsible, to_node, **kwargs):
        super().__init__(responsible=responsible, **kwargs)
        self.destination = to_node

    def prepare(self, **inputs):
        self.inputs = inputs
        self.origin = None

    def execute(self):
        """Create outputs"""
        self.outputs = self.inputs


class Destruct(Flow):
    """Special flow where a item/token is inserted into node"""
    def __init__(self, responsible, from_node, **kwargs):
        super().__init__(responsible=responsible, **kwargs)
        self.origin = from_node

    def prepare(self, inputs):
        self.inputs = inputs

    def execute(self):
        pass


class Movement(Flow):
    """Special flow where a item/token is inserted into node"""
    def __init__(self, responsible, from_node, to_node, **kwargs):
        super().__init__(responsible=responsible, **kwargs)
        self.destination = to_node

    def prepare(self, **inputs):
        self.inputs = inputs

    def execute(self):
        """Create outputs"""
        self.outputs = self.inputs


class Check(Flow):
    """Result a control after execution """
    __mapper_args__ = {'polymorphic_identity': 'check'}

    def __init__(self, test, control, responsible, **kwargs):
        super().__init__(path=control, respon**kwargs)

    def prepare(self):
        self.part = self.parent.inputs['part']
        self.characteristic = self.path.consumption_plan.values()[0]

    def add_measure(self, value, characteristic, tracking='', parent=None):
        measurement = items.Measurement(resource=characteristic, tracking=tracking)
        if parent:
            relation = ItemRelation(relation_class='contains')
            relation.to_node = measurement
            parent.destinations.append(relation)

        self.outputs.append((measurement, value))

    def add_defect(self, failure_mode, tracking='', parent=None):
        self.state = 'nok'

        defect = items.Defect(resource=failure_mode, tracking=tracking)
        if parent:
            relation = ItemRelation(relation_class='contains')
            relation.to_node = defect
            parent.destinations.append(relation)

        self.outputs.append((defect, 1.0))

    def eval_measure(self, value, characteristic,
                     modes=['low', 'high', 'suspicious'],
                     uncertainty=0):

        limits = getattr(characteristic, 'limits', None)
        if limits:
            mode = None

            low_limit = limits[0]
            if low_limit is not None:
                sure_low = low_limit + uncertainty
                if value < sure_low:
                    mode = '{} {}'.format(modes[2],
                                                       modes[0])
                if value < low_limit:
                    mode = modes[0]

            top_limit = limits[1]
            if top_limit is not None:
                sure_top = top_limit - uncertainty
                if value > sure_top:
                    mode = '{} {}'.format(modes[2],
                                                       modes[1])
                if value > top_limit:
                    mode = modes[1]

            if mode:
                failure_mode = characteristic.get_failure_mode(mode)
                return failure_mode

    def terminate(self):
        state = self.state
        super().terminate()

        if state == 'ongoing':
            self.state = 'ok'
        else:
            self.state = state

    def cancel(self):
        super().terminate()
        self.state = 'cancelled'

    @reconstructor
    def after_load(self):
        self.defects = []
        self.measures = []
        for relation in self.destinations:
            item = relation.to_item
            if relation.relation_class == 'contains':
                if item.is_a == 'measure':
                    self.measures.append(item)
                elif item.is_a == 'defect':
                    self.defects.append(item)
            elif relation.relation_class == 'for':
                self.item = item


class Test(Flow):
    """Group of checks following a control plan"""
    __mapper_args__ = {'polymorphic_identity': 'test'}
    control_plan = synonym('path')

    def __init__(self, control_plan, responsible, controller=None):
        Flow.__init__(self, path=control_plan,
                      responsible=responsible,
                      controller=controller)
        self.state = 'started'
        for control in control_plan.children:
            check = Check(control=control, responsible=responsible,
                                       controller=controller)
            self.children.append(check)

    def prepare(self):
        super().prepare()
        self.part = self.in_tokens[0].item
        self.devices = self.path.devices

    def terminate(self):
        super().terminate()

        self.state = self.eval_test_result()

        if self.state != 'ok': # Return all to origin node
            for token in self.out_tokens:
                token.node = self.path.from_node

    def eval_test_result(self):
        state = 'ok'
        for check in self.children:
            if check.state == 'nok':
                state = 'nok'

                break
            elif check.state == 'cancelled':
                state = 'cancelled'
                break
            elif check.state == 'suspicious':
                state = 'suspicious'

        return state
