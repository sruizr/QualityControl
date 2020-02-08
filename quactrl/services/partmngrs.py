import time
import threading
import logging


logger = logging.getLogger(__name__)


class SetupException(Exception):
    pass

class CavityState:

    def __init__(self, cavity):
        self.cavity = cavity

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def handle(self):
        pass


class Empty(CavityState):
    def handle(self):
        if self.cavity.part_is_present():
            self.cavity.part = None
            self.cavity.set_state('loaded')


class Loaded(CavityState):
    def handle(self):
        if not self.cavity.part_is_present():
            self.cavity.set_state('empty')
            return

        if self.cavity.part_is_ready() and self.cavity.inspector.state == 'idle':
            self.cavity.stack_part()
            self.cavity.set_state('stacked')


class Stacked(CavityState):
    def handle(self):
        if self.cavity.inspector.state == 'busy':
            self.cavity.part = self.cavity.inspector.part
            self.cavity.set_state('busy')


class Busy(CavityState):
    def handle(self):
        if self.cavity.inspector.state != 'busy':
            self.cavity.set_state('solved')
            self.cavity.resolution = self.cavity.inspector.state


class Solved(CavityState):
    def handle(self):
        print(self.cavity.part_is_present())
        if not self.cavity.part_is_present():
            self.cavity.set_state('empty')


class Cavity:
    """Cavity where a part is allocated to test
    """
    def __init__(self, part_manager, key=None):
        self.key = key

        self._states = {
            State.__name__.lower(): State(self)
            for State in [Empty, Loaded, Stacked, Busy, Solved]
        }
        self._state = self._states['empty']
        self.test_service = part_manager.test_service
        if key not in self.test_service.inspectors.keys():
            self.test_service.start_inspector(key)

        self.inspector = part_manager.test_service.inspectors[key]
        self.get_part_info = lambda: part_manager.get_part_info(self.key)
        self.part_is_present = lambda: part_manager.part_is_present(self.key)
        self.part_is_ready = lambda: part_manager.is_ready()
        self.part_manager = part_manager
        self.part = None

    def restart(self, reinsert_orders=True):
        self.part_manager.test_service.restart_inspector(self.key,
                                                         reinsert_orders)
    def set_state(self, value):
        if self._state.name != value:
            self._state = self._states[value]
            self.part_manager.cavity_state_has_changed(self.key)

    @property
    def state(self):
        return self._state.name

    def stack_part(self):
         part_info = self.get_part_info()
         self.test_service.stack_part(
                part_info,
                self.part_manager.responsible.key,
                self.key
         )

    def refresh(self):
        """Refresh state of cavity
        """
        self._state.handle()

    def __del__(self):
        self.inspector.stop()


class MultiPartManager(threading.Thread):
    """Base class for all part managers
    """
    def __init__(self, test_service, refresh_time=0):
        super().__init__()
        self.test_service = test_service
        self.data = test_service.db
        self.refresh_time = refresh_time

        self._continue = True
        self.setDaemon(True)

        self.responsible = None
        self.cavities = {}

    def add_cavity(self, key=None):
        self.cavities[key] = Cavity(self, key)

    def remove_cavity(self, key=None):
        cavity = self.cavities.pop(key)
        del(cavity)

    def run(self):
        while self._continue:
            cavities = list(self.cavities.values())
            for cavity in cavities:
                cavity.refresh()

    def stop(self):
        self._continue = False
        self.join()

    def is_ready(self):
        """Return true if it's properly configured
        """
        return self.responsible is not None

    def part_is_present(self, cavity_key):
        """Retrieve true if the part is on the cavity
        """
        raise NotImplementedError()

    def get_part_info(self, cavity_key):
        """Retrieves part number and serial number of loaded part
        """
        raise NotImplementedError()

    def cavity_state_has_changed(self, cavity):
        "Called by cavity when it's state has changed"
        pass

    def set_responsible(self, key):
        if key is None:
            self.responsible = None
        else:
            self.responsible = self.data.Persons().get(key)

    def __del__(self):
        self.stop()


class MonoPartManager(MultiPartManager):
    """Launcher for a tool with only one cavity
    """
    def __init__(self, test_service, refresh_time=0):
        super().__init__(test_service, refresh_time)
        self.add_cavity(None)

    @property
    def cavity(self):
        return self.cavities[None] if None in self.cavities else None
