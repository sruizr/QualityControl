import time
from unittest.mock import Mock, patch, call
from quactrl.services.inspection import (
    Inspector, ControlRunner, InspectionSession, InspectionManager   )
from tests import TestWithPatches
import pytest


pytestmark = pytest.mark.current


# An_InspectionManager(TestWithPatches):
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
