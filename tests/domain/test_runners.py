from tests import TestWithPatches
from quactrl.domain.runners import ControlRunner


class A_ControlRunner(TestWithPatches):

    def setup_method(self, method):
        patches = [
            'quactrl.domain.runners.dal',
            'quactrl.domain.runners.DeviceRepo'
            ]
        self.create_patches(patches)
        # self.control = Mock()
        # self.inspector = Mock()
        self.control_runner = ControlRunner()

    def should_load_device_repo_when_location_is_set(self):
        self.control_runner.set_location('loc_key')

        self.DeviceRepo.assert_called_with('loc_key')
        assert self.control_runner.devices == self.DeviceRepo()

    # def should_start_test_from_part_info(self):
    #     pass


    # def should_init_loading_method(self):
    #     method_repo = self.inspector.service.env.method_repo

    #     assert self.control_runner.method == method_repo.get.return_value
    #     method_repo.get.assert_called_with(self.control.method_name)

    # def should_count(self):
    #     self.control.sampling.check_is_needed.return_value = False
    #     assert self.control_runner.count() is None

    #     self.control.sampling.check_is_needed.return_value = True
    #     assert self.patch['Check'].return_value == self.control_runner.count()
    #     part = self.inspector.current_part
    #     self.patch['Check'].assert_called_once_with(self.inspector.test,
    #                                                 self.control, part)

    # def should_run_method(self):
    #     check = Mock()
    #     method = self.inspector.service.env.method_repo.get.return_value

    #     self.control_runner.run_method(check)
    #     method.assert_called_once_with(self.inspector, check)
