from threading import Event
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import synonym, reconstructor
from quactrl.domain.base import (Resource, PathResource, Path, Node, Pars,
                                 Flow
                                 )



class Creation(Flow):
    """Special flow where a item/token is inserted into node"""
    __mapper_args__ = {'polymorphic_identity': 'creation'}

    def __init__(self, responsible, **kwargs):
        super().__init__(responsible=responsible, **kwargs)


    def run(self, to_node, *items):
        super().start()

        self.destination = to_node
        self.outputs = items

        super().finish()
        super().close()


class Destruction(Flow):
    """Special flow where a item/token is remove from node"""
    __mapper_args__ = {'polymorphic_identity': 'destruction'}

    def __init__(self, responsible, **kwargs):
        super().__init__(responsible=responsible, **kwargs)

    def run(self, from_node, *items):
        super().start()

        self.origin = from_node
        self.inputs = items

        super().finish()
        super().close()


class Movement(Flow):
    """Special flow where a item/token is inserted into node"""
    __mapper_args__ = {'polymorphic_identity': 'movement'}

    def __init__(self, responsible, **kwargs):
        super().__init__(responsible=responsible, **kwargs)

    def run(self, from_node, to_node, *items):
        super().start()

        self.inputs = self.outputs = items
        self.origin = from_node
        self.destination = to_node

        super().finish()
        super().close()


class Test(Flow):
    """Group of checks following a control plan"""
    __mapper_args__ = {'polymorphic_identity': 'test'}
    control_plan = synonym('path')

    # def __init__(self, control_plan, responsible, controller=None):
    #     Flow.__init__(self, path=control_plan,
    #                   responsible=responsible,
    #                   controller=controller)
    #     self.state = 'started'
    #     for control in control_plan.children:
    #         check = Check(control=control, responsible=responsible,
    #                                    controller=controller)
    #         self.children.append(check)

    def prepare(self):
        super().prepare()
        self.part = self.in_tokens[0].item
        self.devices = self.path.devices

    def terminate(self):
        super().terminate()

        self.state = self.eval_test_result()

        if self.state != 'ok':  # Return all to origin node
            for token in self.out_tokens:
                token.node = self.path.from_node

    def op_creator(self):
        for step in self.path.steps:
            yield step.create_operation(self)

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


class Check(Flow):
    """Execute a control with ok - nok result"""
    __mapper_args__ = {'polymorphic_identity': 'check'}

    @hybrid_property
    def test(self):
        return self.flow

    @test.setter
    def test(self, flow):
        self.flow = flow
        self.origin = self.flow.path.from_node if self.path else None
        self.destination = self.flow.path.to_node if self.path else None

    def run(self):
        super().start()
        self.test.tester.notify(self)

        try:
            super().execute()
            if self._has_thread_alive():
                self.state == 'ongoing'
                self.test.tester.notify(self)
                self.finished = Event()
                self.finished.wait()
        except Exception as e:
            self.cancel()
            raise e

        super().finish()
        if self.state == 'finished':
            self.state = 'ok'
        self.test.tester.notify(self)

    def cancel(self):
        self.state = 'cancelled'
        if self._has_thread_alive():
            self.thread.cancel()
            self.finished.set()

    def _has_thread_alive(self):
        return hasattr(self, 'thread') and self.thread.is_alive()

    def clean_old_defects(self):
        part = self.test.part
        for defect in part.defects:
            if defect.avalaible_tokens and defect.avalaible_tokens[0].producer.path == self.path:
                defect.qty = None
                self.inputs.append(defect)

    def track_devices(self, **devices):
        dev_trackings = []
        for device in devices:
            dev_trackings = device.tracking
        self.tracking = '&'.join(dev_trackings)

    def add_measure(self, value, characteristic, element_key='', parent=None):
        """Helper for adding measures to part"""
        self.test
        measurement = items.Measurement(resource=characteristic, tracking=tracking)
        if parent:
            relation = ItemRelation(relation_class='contains')
            relation.to_node = measurement
            parent.destinations.append(relation)

        self.outputs.append((measurement, value))

    # def add_defect(self, failure_mode, tracking='', parent=None):
    #     """Helper for adding defects to part"
    #     self.state = 'nok'

    #     defect = items.Defect(resource=failure_mode, tracking=tracking)
    #     if parent:
    #         relation = ItemRelation(relation_class='contains')
    #         relation.to_node = defect
    #         parent.destinations.append(relation)

    #     self.outputs.append((defect, 1.0))

    # def eval_measure(self, value, characteristic,
    #                  modes=['low', 'high', 'suspicious'],
    #                  uncertainty=0):

    #     limits = getattr(characteristic, 'limits', None)
    #     if limits:
    #         mode = None

    #         low_limit = limits[0]
    #         if low_limit is not None:
    #             sure_low = low_limit + uncertainty
    #             if value < sure_low:
    #                 mode = '{} {}'.format(modes[2],
    #                                                    modes[0])
    #             if value < low_limit:
    #                 mode = modes[0]

    #         top_limit = limits[1]
    #         if top_limit is not None:
    #             sure_top = top_limit - uncertainty
    #             if value > sure_top:
    #                 mode = '{} {}'.format(modes[2],
    #                                                    modes[1])
    #             if value > top_limit:
    #                 mode = modes[1]

    #         if mode:
    #             failure_mode = characteristic.get_failure_mode(mode)
    #             return failure_mode
