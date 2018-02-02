import time
from queue import Queue
from unittest.mock import Mock, patch, call
from quactrl.services.inspection import (
    OnePieceFlowService, PullRunner, PushRunner, ProcessRunner,
    Inspector, ControlRunner, InspectionSession, InspectionManager, MethodRepo
    )
import pytest


pytestmark = pytest.mark.current


class TestWithPatches:
    def create_patches(self, definitions):
        self.patch = {}
        self._patchers = []
        for definition in definitions:
            patcher = patch(definition)
            name = definition.split('.')[-1]
            self.patch[name] = patcher.start()
            self._patchers.append(patcher)
            setattr(self, name, self.patch[name])

    def teardown_method(self, method):
        for patcher in self._patchers:
            patcher.stop()


class A_OnePieceFlowService(TestWithPatches):
    def setup_method(self, method):
        self.create_patches([
            'quactrl.services.inspection.LocationQueue',
            'quactrl.services.inspection.PullRunner',
            'quactrl.services.inspection.Generator',
            'quactrl.services.inspection.InsertPartError'
            ])
        self.env = Mock()
        self.opf = OnePieceFlowService(self.env)

        self.Generator = self.patch['Generator']
        self.Operation = self.patch['PullRunner']
        self.Location = self.patch['LocationQueue']
        self.InsertPartError = self.patch['InsertPartError']

    def should_init_with_environment(self):
        opf = self.opf

        dal = self.env.dal

        assert opf.responsible is None
        assert opf.dal == dal
        assert opf.operation == self.Operation.return_value
        assert opf.generator == self.Generator.return_value
        assert opf.location == self.Location.return_value
        # assert
        # assert self.opf.dal == self.env.dal
        # assert self.opf.view == self.env.view
        # assert self.opf.resource is None
        # assert self.opf.main_operation is None
        # assert self.opf.generator is None

    def should_enter_part(self):
        item_data = {'tracking': '123456',
                     'resource_key': 'partnumber'}
        responsible = 'john'

        opf = self.opf
        opf.location.try_load.return_value = False
        opf.generator.is_loaded.return_value = False

        opf.enter_part(item_data, responsible)

        assert opf.responsible == opf.dal.do.get_person.return_value
        opf.dal.do.get_person.assert_called_with(responsible)

        opf.controller.notify_error.assert_called_with(
            self.InsertPartError(), **item_data
            )

        opf.generator.is_loaded.return_value = True
        opf.enter_part(item_data, responsible)

        opf.generator.origin.put.assert_called_with((item_data, opf.responsible))

    def should_start(self):
        opf = self.opf
        opf.operation = Mock()
        opf.generator = Mock()

        opf.generator.is_loaded.return_value = False
        self.opf.start()

        assert opf.operation.start.called
        assert not opf.generator.start.called

        opf.generator.is_loaded.return_value = True
        opf.start()

        assert opf.generator.start.called

    def should_stop(self):
        self.opf.stop()
        assert self.opf.stop_event.is_set()

class Stuff:
    pass

def test_method_repo():
    assert MethodRepo.get('test') is None
    assert MethodRepo.get('tests.services.test_inspection.Stuff') == Stuff


class A_ProcessRunner(TestWithPatches):
    def setup_method(self, method):
        self.create_patches([
            'quactrl.services.inspection.LocationQueue'
        ])
        self.dal = Mock()
        self.stop_event = Mock()
        self.controller = Mock()
        self.runner = ProcessRunner(self.dal, self.stop_event,
                                    self.controller)

    def should_init_properly(self):
        runner = self.runner
        assert runner.dal == self.dal
        assert runner.stop_event == self.stop_event
        assert runner.controller == self.controller

        runner = ProcessRunner(self.dal)

        assert runner.stop_event is None
        assert runner.controller is None

    def should_run(self):
        runner = self.runner

        runner.origin = Mock()
        runner.origin.get.side_efect = [(Mock(), 'r'), None]
        runner.destination = Mock()
        runner.load_process = Mock()
        runner.process = Mock()

        self.stop_event.is_set.return_value = False
        runner.start()
        time.sleep(1)
        self.stop_event.is_set.return_value = True
        assert runner.process.close.called
        assert self.controller.notify_process_finished.called


        # class An_InspectionManager(TestWithPatches):
#     def setup_method(self, method):
#         self.env = Mock()
#         self.im = InspectionManager(self.env)
#         self.create_patches([
#             'quactrl.services.inspection.Inspector'
#             ])

#     def should_set_process(self):
#         process = 'process name'
#         self.im.set_process(process)
#         assert self.im.process == process
#         assert self.env.device_repo.set_process.called

#     def should_setup_batch(self):
#         batch = Mock()
#         control_repo = self.env.control_repo
#         plans = [Mock() for _ in range(3)]
#         control_repo.get.return_value = plans
#         for plan in plans:
#             plan.resolution = 0
#             plan.inspectors = 1
#         plans[2].inspectors = 2

#         assert self.im.batch is None
#         self.im.setup_batch(batch)

#         assert len(self.im.inspectors) == 4
#         assert self.im.batch == batch
#         control_repo.get.assert_called_with(self.im.process, batch.partnumber)

#         inspector_calls = self.patch['Inspector'].return_value.setup_batch.mock_calls
#         expected_plans = [plans[0], plans[1], plans[2], plans[2]]
#         for inspector, plan in zip(self.im.inspectors, expected_plans):
#             assert call(plan.controls, 0) in inspector_calls
#             inspector.session.start.assert_called_with()

#     @pytest.mark.ahora
#     def should_receive_part(self):
#         self.im.inspectors = [Mock() for _ in range(3)]
#         self.im.setup_batch = Mock()

#         part = Mock()
#         self.im.receive_part(part, 1)

#         self.im.setup_batch.assert_called_once_with(part.batch)
#         self.im.inspectors[1].receive_part.assert_called_once_with(part)


# class An_InspectionSession(TestWithPatches):

#     def setup_method(self, method):
#         self.inspector = Mock()
#         self.inspector.parts_queue = Queue()
#         self.inspector.control_runners = [Mock() for _ in range(30)]
#         self.create_patches([
#             'quactrl.services.inspection.Test'
#             ])

#     def should_work_on_continuous(self):
#         try:
#             inspection_session = InspectionSession(self.inspector, resolution=1)
#             inspection_session.start()
#             assert inspection_session.is_alive()
#         except Exception as e:
#             raise e
#         finally:
#             inspection_session.stop()
#             assert not inspection_session.is_alive()

#     def should_work_on_cycles(self):
#         try:
#             inspection_session = InspectionSession(self.inspector)

#             inspection_session.start()
#             assert not self.inspector.control_runners[0].run.called

#             self.inspector.parts_queue.put(None)
#             time.sleep(0.25)
#             assert self.inspector.service.check_initialized.called
#             assert self.inspector.service.check_finished.called
#         except Exception as e:
#             raise e
#         finally:
#             inspection_session.stop()
#             assert not inspection_session.is_alive()

#     def should_stop_cycle_when_async_method(self):
#         try:
#             # control_runners[5] has an async method
#             check = Mock(name='check')
#             check.state = 'ongoing'
#             self.inspector.control_runners[5].count.return_value = check
#             self.inspector.control_runners[5].run = lambda s: time.sleep(0.5)

#             inspection_session = InspectionSession(self.inspector)
#             inspection_session.start()
#             self.inspector.parts_queue.put(None)
#             time.sleep(0.25)
#             assert not self.inspector.control_runners[6].run.called

#             inspection_session.stop_cycle()
#             time.sleep(1)
#             assert check.cancel.called
#             assert self.inspector.test.state == 'cancelled'
#             assert check.state == 'cancelled'

#             assert not self.inspector.control_runners[6].run.called
#         except Exception as e:
#             raise e
#         finally:
#             inspection_session.stop()
#             assert not inspection_session.is_alive()

#     def should_stop_cycle_on_mid_sequence(self):
#         try:
#             self.inspector.control_runners[5].run = lambda: time.sleep(0.5)

#             inspection_session = InspectionSession(self.inspector)
#             inspection_session.start()
#             self.inspector.parts_queue.put(None)
#             time.sleep(0.25)
#             assert not self.inspector.control_runners[6].run.called

#             inspection_session.stop_cycle()
#             assert not self.inspector.control_runners[6].run.called
#         except Exception as e:
#             raise e
#         finally:
#             inspection_session.stop()
#             assert not inspection_session.is_alive()

# class An_Inspector(TestWithPatches):

#     def setup_method(self, method):
#         patches = [
#             'quactrl.services.inspection.time',
#             'quactrl.services.inspection.Test',
#             'quactrl.services.inspection.Check',
#             'quactrl.services.inspection.InspectionSession',
#             'quactrl.services.inspection.ControlRunner'
#             ]
#         self.create_patches(patches)
#         self.service = Mock()

#     def should_init_properly(self):
#         inspector = Inspector(self.service)
#         assert inspector.service == self.service

#     def should_setup_batch(self):
#         inspector = Inspector(self.service)
#         controls = [Mock() for _ in range(3)]
#         assert len(inspector.control_runners) == 0

#         inspector.setup_batch(controls)

#         assert self.patch['ControlRunner'].call_count == 3
#         assert len(inspector.control_runners) == 3

#     def should_eval_value(self):
#         inspector = Inspector(self.service)
#         characteristic = Mock()
#         characteristic.limits = [-1, 1]
#         modes = ['very low', 'very high', 'a bit suspicious']
#         uncertainty = 0.2
#         # TODO: Check if one of the limits is ommited
#         value = 0
#         failure_mode = inspector.eval_value(value, characteristic,
#                                                  uncertainty, modes)
#         assert failure_mode is None

#         value = 0.81
#         failure_mode = inspector.eval_value(value, characteristic,
#                                                  uncertainty, modes)
#         self.service.env.repo_fry.get.return_value.get.assert_called_with(
#             'a bit suspicious very high', characteristic)

#         value = 1.1
#         failure_mode = inspector.eval_value(value, characteristic,
#                                                  uncertainty, modes)
#         self.service.env.repo_fry.get.return_value.get.assert_called_with(
#             'very high',
#             characteristic)

#         value = -0.81
#         failure_mode = inspector.eval_value(value, characteristic,
#                                                  uncertainty, modes)
#         self.service.env.repo_fry.get.return_value.get.assert_called_with(
#             'a bit suspicious very low', characteristic)

#         value = -1.1
#         failure_mode = inspector.eval_value(value, characteristic,
#                                             uncertainty, modes)
#         self.service.env.repo_fry.get.return_value.get.assert_called_with(
#             'very low', characteristic)


# class A_ControlRunner(TestWithPatches):

#     def setup_method(self, method):
#         patches = [
#             'quactrl.services.inspection.Check'
#             ]
#         self.create_patches(patches)
#         self.control = Mock()
#         self.inspector = Mock()
#         self.control_runner = ControlRunner(self.inspector, self.control)

#     def should_init_loading_method(self):
#         method_repo = self.inspector.service.env.method_repo

#         assert self.control_runner.method == method_repo.get.return_value
#         method_repo.get.assert_called_with(self.control.method_name)

#     def should_count(self):
#         self.control.sampling.check_is_needed.return_value = False
#         assert self.control_runner.count() is None

#         self.control.sampling.check_is_needed.return_value = True
#         assert self.patch['Check'].return_value == self.control_runner.count()
#         part = self.inspector.current_part
#         self.patch['Check'].assert_called_once_with(self.inspector.test,
#                                                     self.control, part)

#     def should_run_method(self):
#         check = Mock()
#         method = self.inspector.service.env.method_repo.get.return_value

#         self.control_runner.run_method(check)
#         method.assert_called_once_with(self.inspector, check)
