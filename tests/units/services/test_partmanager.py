from unittest.mock import Mock, patch
from quactrl.services.partmngrs import Cavity, Empty, Loaded, Stacked, Busy, Solved



class A_Cavity:
    def setup_method(self, method):
        part_manager = Mock()
        part_manager.test_service.inspectors = {0: Mock()}
        key = 0
        self.cavity = Cavity(part_manager, key)

    def should_start_empty(self):

        assert self.cavity.state == 'empty'


    def should_be_loaded(self):
        self.cavity.part_manager.part_is_present.return_value = False
        self.cavity.refresh()
        assert self.cavity.state != 'loaded'

        self.cavity.part_manager.part_is_present.return_value = True
        self.cavity.refresh()
        assert self.cavity.state == 'loaded'

    def should_return_to_empty_if_part_is_not_present(self):
        self.cavity.set_state('loaded')
        self.cavity.part_manager.part_is_present.return_value = False

        self.cavity.refresh()

        assert self.cavity.state == 'empty'

    def should_go_to_stacked_if_inspector_is_ready(self):
        self.cavity.set_state('loaded')
        self.cavity.part_manager.test_service.inspectors[0].state = 'idle'
        self.cavity.part_manager.is_ready.return_value = False

        self.cavity.refresh()

        assert self.cavity.state == 'loaded'

        self.cavity.part_manager.is_ready.return_value = True
        self.cavity.refresh()

        assert self.cavity.state == 'stacked'

    def should_busy_after_inspector_confirmation(self):
        self.cavity.set_state('stacked')

        self.cavity.inspector.state = 'busy'

        self.cavity.refresh()

        assert self.cavity.state == 'busy'
        assert self.cavity.part

    def should_resolve_after_inspector_confirmation(self):
        self.cavity.set_state('busy')
        self.cavity.inspector.state = 'resolution'

        self.cavity.refresh()

        assert self.cavity.state == 'solved'
        assert self.cavity.resolution == 'resolution'

    def should_empty_when_unload_part(self):
        self.cavity.set_state('solved')
        self.cavity.part_is_present.return_value = False
        self.cavity.part_manager.part_is_present.return_value = False

        self.cavity.refresh()

        assert self.cavity.part is None
        assert self.cavity.state == 'empty'
