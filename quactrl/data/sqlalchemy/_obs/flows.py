from threading import Event
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import synonym, reconstructor
from quactrl.domain.base import (Resource, PathResource, Path, Node, Pars,
                                 Flow
                                 )
import quactrl.domain.items as i


class Creation(Flow):
    """Special parent where a item/token is inserted into node"""
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
    """Special parent where a item/token is remove from node"""
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
    """Special parent where a item/token is inserted into node"""
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


class WithTester:
    """Mixin with tester property"""
    @property
    def tester(self):
        if hasattr(self, '_test'):
            return self._test
        else:
            return None

    @tester.setter
    def tester(self, value):
        self._tester = value

    def notify(self):
        if self._tester:
            self.tester.update(self)


class Test(Flow, WithTester):
    """Group of checks following a control plan"""
    __mapper_args__ = {'polymorphic_identity': 'test'}

    # def __init__(self, control_plan, responsible, controller=None):
    #     Flow.__init__(self, path=control_plan,
    #                   responsible=responsible,
    #                   controller=controller)
    #     self.state = 'started'
    #     for control in control_plan.children:
    #         check = Check(control=control, responsible=responsible,
    #                                    controller=controller)
    #         self.children.append(check)


    def start(self, part):
        super().start()
        self.inputs.append(part.avalaible_tokens[0])
        self.part = self.inputs[0].item
        self.devices = self.path.devices
        self.notify()

    def terminate(self):
        super().terminate()

        self.state = self.eval_test_result()

        if self.state != 'ok':  # Return all to origin node
            for token in self.out_tokens:
                token.node = self.path.from_node

        self.notify()

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


class Check(Flow, WithTester):
    """Execute a control with ok - nok result"""
    __mapper_args__ = {'polymorphic_identity': 'check'}

    @hybrid_property
    def test(self):
        return self.parent

    @test.setter
    def test(self, test):
        self.parent = test

    @hybrid_property
    def control(self):
        return self.path

    @control.setter
    def control(self, control):
        return self.path

    def run(self):
        super().start()
        self.notify()

        self.part = self.test.part
        try:
            super().execute()
            if self._has_thread_alive():
                self.state == 'ongoing'
                self.notify()
                self.finished = Event()
                self.finished.wait()
        except Exception as e:
            self.cancel()
            self.notify()
            raise e

        super().finish()
        if self.state == 'finished':
            self.state = 'ok'
        self.notify_observers()

    def cancel(self):
        self.state = 'cancelled'
        if self._has_thread_alive():
            self.thread.cancel()
            self.finished.set()

    def _has_thread_alive(self):
        return hasattr(self, 'thread') and self.thread.is_alive()

    def add_measure(self, value, characteristic, element_key=None):
        """Helper for adding measures to part"""
        part = self.part

        tracking = self._compose_tracking(part, characteristic, element_key)
        measurement = self._find_by_tracking(part.measurements, tracking)
        if not measurement:
            measurement = i.Measurement(part, characteristic, tracking=tracking)
        measurement.qty = value
        self.outputs.append(measurement)
        return measurement

    def add_defect(self, failure_mode, element_key=None, qty=1.0):
        part = self.part
        tracking = self._compose_tracking(part, failure_mode, element_key)
        defect = self._find_by_tracking(part.defects, tracking)
        if not defect:
            defect = i.Defect(part, failure_mode)
            defect.tracking = tracking

        defect.qty = qty
        self.outputs.append(defect)

        return defect

    def _find_by_tracking(self, items, tracking):
        if tracking not in [item.tracking for item in items]:
            return
        else:
            for item in items:
                if item.tracking == tracking:
                    return item

    def _compose_tracking(self, part, resource, element_key):
        tracking = '{}*{}'.format(part.tracking, resource.key)
        tracking = '{}[{}]'.format(tracking, element_key) if element_key else tracking
        return tracking

    def clean_old_defects(self):
        for defect in self.part.defects:
            if defect.avalaible_tokens and defect.avalaible_tokens[0].producer.path == self.path:
                defect.qty = None
                self.inputs.append(defect)

    def track_devices(self, *devices):
        dev_trackings = []
        for device in devices:
            dev_trackings.append(device.tracking)
        self.tracking = '&'.join(dev_trackings)
