import time
import threading
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
            # logger.debug('Has part {}'.format(
            #     self.cavity.part_manager._part_info))


class Waiting(CavityState):
    def handle(self):
        if self.cavity.inspector.state == 'busy':
            self.cavity.set_state('busy')


class Loaded(CavityState):
    def handle(self):
        if not self.cavity.part_is_present():
            self.cavity.set_state('empty')
            logger.debug('Has part {}'.format(
                self.cavity.part_manager._part_info))
            return

        if (self.cavity.part_is_ready() and
                self.cavity.inspector.state == 'idle'):
            self.cavity.stack_part()
            self.cavity.set_state('stacked')


class Stacked(CavityState):
    def handle(self):
        if self.cavity.inspector.part_sn == self.cavity.part_sn:
            self.cavity.part = self.cavity.inspector.part
            self.cavity.set_state('busy')


class Busy(CavityState):
    def handle(self):
        if self.cavity.inspector.state == 'waiting':
            self.cavity.set_state('waiting')
        elif self.cavity.inspector.state != 'busy':
            self.cavity.set_state('solved')


class Solved(CavityState):
    def handle(self):
        if not self.cavity.part_is_present():
            self.cavity.set_state('empty')


class Cavity:
    """Cavity where a part is allocated to test
    """
    def __init__(self, part_manager, key=None):
        self.key = key

        self._states = {
            State.__name__.lower(): State(self)
            for State in [Empty, Loaded, Stacked, Busy, Solved, Waiting]
        }
        self._state = self._states['empty']
        self.test_service = part_manager.test_service
        if key not in self.test_service.inspectors.keys():
            self.test_service.start_inspector(key)
        self.inspector = part_manager.test_service.inspectors[key]

        self._part = None
        self.get_part_info = lambda: part_manager.get_part_info(self)
        self.part_is_present = lambda: part_manager.part_is_present(self)
        self.part_is_ready = lambda: part_manager.is_ready()
        self.part_manager = part_manager
        self.resolution = None
        self._part_sn = None

    @property
    def part(self):
        if self.state in ('busy', 'iddle'):
            return self._part

    @part.setter
    def part(self, value):
        self._part = value

    def restart(self, reinsert_orders=True):
        self.part_manager.test_service.restart_inspector(self.key,
                                                         reinsert_orders)

    def set_state(self, value):
        if self._state.name != value:
            self._state = self._states[value]
            if value == 'solved':
                self.resolution = self.inspector.test.status
                logger.info('Resolution on cavity {} is {}'.format(
                    self.key, self.resolution
                ))
            elif value in ('loaded', 'stacked', 'busy'):
                self.resolution = None
            self.part_manager.cavity_state_has_changed(self)
            logger.info('Cavity {} has changed to {}'.format(
                self.key, self.state))

    @property
    def state(self):
        return self._state.name

    def stack_part(self):
        part_info = self.get_part_info()
        self.part_sn = part_info['serial_number']
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
    def __init__(self, test_service, refresh_time=0.2):
        super().__init__()
        self.test_service = test_service
        self.data = test_service.dal
        self.refresh_time = refresh_time
        self.create_part = True

        self._continue = True
        self.setDaemon(True)

        self.responsible = None
        self.cavities = {}

    def add_cavity(self, key=None):
        """Add new cavity for allocating part
        """
        self.cavities[key] = Cavity(self, key)

    def remove_cavity(self, key=None):
        cavity = self.cavities.pop(key)
        del(cavity)

    def run(self):
        while self._continue:
            cavities = list(self.cavities.values())
            for cavity in cavities:
                cavity.refresh()
            time.sleep(self.refresh_time)

    def start(self, tff=False):
        self.test_service.create_part = self.create_part
        self.test_service.tff = tff

        super().start()

    def stop(self):
        self._continue = False
        self.join()

    def is_ready(self):
        """Return true if it's properly configured
        """
        return self.responsible is not None

    def part_is_present(self, cavity):
        """Retrieve true if the part is on the cavity
        """
        raise NotImplementedError()

    def get_part_info(self, cavity):
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
        if self.responsible:
            logger.debug('Responsible is set to {}'.format(self.responsible))

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
