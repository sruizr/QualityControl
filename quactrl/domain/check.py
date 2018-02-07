from enum import Enum
from sqlalchemy.orm import synonym, reconstructor
from threading import Thread, Event
from quactrl.domain.erp import (Item, Resource, PathResource,
                                ItemRelation, Path, Node, Pars, Flow)
from datetime import datetime


class Result(Enum):
    PENDING = 0
    ONGOING = 1
    SUSPICIOUS = 2
    NOK = 2
    CANCELLED = 8
    OK = 10


class Sampling(Enum):
    ongoing = 0
    every_unit = 1

    each_10 = 21
    each_100 = 22
    each_1000 = 23
    each_10000 = 24
    each_100000 = 25

    by_second = 30
    by_minute = 31
    by_hour = 32
    by_day = 33
    by_week = 34
    by_month = 35
    by_year = 36


class ControlPlan(Path):
    __mapper_args__ = {'polymorphic_identity': 'control_plan'}

    def __init__(self, name='Plan for testing 100% pars', method_name='quactrl.methods.by_pass', pars=None, **kwargs):
        super().__init__(**kwargs)
        self.method_name = method_name
        self.name = name
        if pars:
            self.pars = Pars(pars)

    @reconstructor
    def after_load(self):
        pass

    def create_flow(self, responsible, controller=None):
        return Test(self, responsible, controller)


class Control(Path):
    __mapper_args__ = {'polymorphic_identity': 'control'}

    characteristic = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @reconstructor
    def after_load(self):
        pass

    def add_characteristic(self, characteristic, **pars):

        path_resource = PathResource(self, characteristic, 'out', pars=pars)
        self.resource_list.append(path_resource)

    def create_flow(self, test, responsible):
        return Check(self, test, responsible, self.controller)

    def set_pars(self, pars):
        if self.pars:
            self.pars.set(pars)
        else:
            self.pars = Pars(pars)

    def get_pars(self):
        if self.pars:
            return self.pars.get()


class Check(Flow):
    """Result a control after execution """
    __mapper_args__ = {'polymorphic_identity': 'check'}

    control = synonym('path')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.defects = []
        self.measures = []

    def prepare(self):
        self.characteristics = {}
        for res_rel in self.path.resource_list:
            if res_rel.flow == 'out':
                characteristic = res_rel.resource
                if res_rel.pars:
                    limits  = res_rel.pars.get().get('limits')
                    if limits:
                        characteristic.limits = limits
                self.characteristics[characteristic.key] = characteristic

        self.part = self.parent.part
        self.devices = self.parent.path.devices

    def add_measure(self, characteristic, value, tracking='', parent=None):
        measurement = Measurement(resource=characteristic, tracking=tracking)
        if parent:
            relation = ItemRelation(relation_class='contains')
            relation.to_node = measurement
            parent.destinations.append(relation)

        self.outputs.append((measurement, value))

    def add_defect(self, failure_mode, tracking='', parent=None):
        self.state = 'nok'

        defect = Defect(resource=failure_mode, tracking=tracking)
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

        self.state = state


class Defect(Item):
    __mapper_args__ = {'polymorphic_identity': 'defect'}
    failure_mode = synonym('resource')


class Measurement(Item):
    __mapper_args__ = {'polymorphic_identity': 'measurement'}
    characteristic = synonym('resource')


class DataAccessModule:
    def __init__(self, dal):
        pass
