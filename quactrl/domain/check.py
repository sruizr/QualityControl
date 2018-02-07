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

    def __init__(self, method_name, name='', controller=None, pars=None, **kwargs):
        super().__init__(**kwargs)
        self.method_name = method_name
        self.name = name
        if pars:
            self.pars = Pars(pars)

    @reconstructor
    def after_load(self):
        pass

    def add_characteristic(self, characteristic, **pars):

        path_resource = PathResource(self, characteristic, 'out', pars=pars)
        self.resource_list.append(path_resource)

    def create_flow(self, test, responsible):
        return Check(self, test, responsible, self.controller)


class Check(Flow):
    """Result a control after execution """
    __mapper_args__ = {'polymorphic_identity': 'check'}

    def __init__(self, control, test, responsible, controller=None, **kwargs):
        super().__init__(path=control, parent=test, responsible=responsible, controller=controller, **kwargs)

        self.defects = []
        self.measures = []

    def prepare(self):
        self.characteristics = {}
        for res_rel in self.path.resource_list:
            if res_rel.flow == 'out':
                characteristic = res_rel.resource
                self.characteristics[characteristic.key] = characteristic
        self.part = self.parent.part
        self.devices = self.parent.path.devices

    def add_measure(self, characteristic, value):
        self.measures.append(
            Measure(self.item, self, characteristic, value)
            )

    def add_defect(self, failure_mode):
        self.defects.append(
            Defect(self.item, self, failure_mode)
            )

    def terminate(self):

        if len(self.defects) == 0:
            self.state = 'ok'
        else:
            self.state = 'nok'


    def cancel(self):
        self.state = 'cancelled'
        self.update_view()

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
            self.children.append(Check(test=self, control=control, responsible=responsible,
                                       controller=controller))
    def prepare(self):
        super().prepare()
        self.part = self.inputs[0].item
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

    def __init__(self, checked_item, check, failure_mode):
        self.failure_mode = failure_mode

        # Links check with defect result
        self.check = check
        ItemRelation(
            from_item=check, to_item=self,
            relation_class='contains'
            )

        # Links item with its defect
        self.item = checked_item
        ItemRelation(
            from_item=checked_item, to_item=self,
            relation_class='contains'
            )


class Measure(Item):
    __mapper_args__ = {'polymorphic_identity': 'measure'}
    characteristic = synonym('resource')

    def __init__(self, measured_item, check, characteristic, value):
        self.characteristic = characteristic

        # Link check with measure as check result
        self.check = check
        ItemRelation(
            from_item=check, to_item=self,
            relation_class='contains'
            )

        # Link measured item with measure
        self.item = measured_item
        ItemRelation(
            from_item=measured_item, to_item=self,
            relation_class='contains'
            )

        self.value = value
        check.control.insert_item(self, qty=value)

    @reconstructor
    def after_load(self):
        self.value = self.movements[-1].qty

    # sample = Column(Integer)
    # verifier = Column(String)
    # state = Column(Integer)
    # checks = []
    # # open_date = Column(Datetime)

    # def __init__(self, part, verifier, process, control_plan):
    #     self.verifier = verifier
    #     self.process = process
    #     self.state = Result.PENDING
    #     for control in self.controls:
    #         check = Check(self, control)
    #         self.checks.append(check)

    #     self.session = dal.Session()
    #     self.session.add(self)
    #     self.session.commit()

    #     self.current_check_index = None
    #     self.observers = []

    # def execute(self):
    #     """Run sequence of tests sequentially"""

    #     if self.current_check_index is None:
    #         self.current_check_index = 0

    #     try:
    #         check = self.checks[self.current_check_index]
    #         check.execute()
    #     except Exception as e:
    #         self.close()
    #         raise e

    # def update(self, check, progress=100):
    #     self.notify(check, progress)

    #     if self.state == Result.CANCELLED:
    #         return None

    #     if progress == 100:
    #         self.current_check_index += 1
    #         if self.current_check_index == len(self.checks):
    #             # check sequence  is finished
    #             self.current_check_index = None
    #             self.close()
    #         else:
    #             self.execute()




# class Measurement(Model):
#     __mapper_args__ = {'polymorphic_identity': 'measurement'}

#     check_id = Column(Integer, ForeignKey('check.id'))
#     characteristic_id = Column(Integer, ForeignKey('characteristic.id'))
#     value = Column(DECIMAL)
#     index = Column(Integer)


# class Failure(Item):
#     __mapper_args__ = {'polymorphic_identity': 'failure'}


# class Check(Model):
#     __tablename__ = 'check'
#     control = Column(Integer)
#     test_id = Column(Integer, ForeignKey('test.id'))
#     result = Column(Integer)
#     state = Column(Integer)


#     failures = relationship('Failure', backref='check')
#     measures = relationship('Measurement', backref='check')

#     def __init__(self, test, control):
#         self.open_date = datetime.now()
#         self.test = test
#         self.control = control

#         self.method = method_factory.get_method(control.method)

#         self.state = Result.PENDING
#         self.failures = []
#         self.measures = dict()

#     def add_failure(self, f_mode, characteristic, item, device):
#         """Append failures to checks"""
#         failure = Failure(f_mode, characteristic, item, device)
#         self.failures.append(failure)

#     def get_measure(self, characteristic, item=None, device=None):
#         """Get stored measure from characteristic"""
#         pass

#     def add_measure(self, value, characteristic, item=None, device=None):
#         """Append measurements to measures"""
#         measure = Measure(value, characteristic, item, device)
#         self.measures.append(measure)

#     def process_results(self):
#         """"Persist measures and failures and state final result of check"""
#         if self.failures == []:
#             self.state = Result.OK
#         else:
#             self.state = Result.NOK

#     def close(self, observer=None):
#         """Execute the check"""
#         self.open_date = datetime.now()
#         self.state = Result.ONGOING
#         self.method()
#         self.process_results()
#         self.close_date = datetime.now()


class DataAccessModule:
    def __init__(self, dal):
        pass
