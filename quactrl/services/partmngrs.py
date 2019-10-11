import time
import threading
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SetupException(Exception):
    pass


class Cavity:
    """Cavity where a part is allocated to test
    """
    def __init__(self, part_manager, key=None):
        self.key = key
        self.state = 'empty'

        self.test_service = part_manager.test_service
        if key not in self.test_service.inspectors.keys():
            self.test_service.start_inspector(key)

        self.inspector = part_manager.test_service.inspectors[key]
        self.get_part_info = lambda key: part_manager.get_part_info(key)
        self.part_is_present = lambda key: part_manager.part_is_present(key)
        self.part_manager = part_manager
        self.current_part = None

    @property
    def part(self):
        if self.state in ('busy', 'iddle'):
            return self.current_part

    def restart(self, reinsert_orders=True):
        self.part_manager.test_service.restart_inspector(self.key,
                                                         reinsert_orders)

    def refresh(self):
        """Refresh state of cavity
        """

        state = self.state
        inspector_state = self.inspector.state
        logger.debug('Inspector state is {} and state is  {}'.format(
            inspector_state, state
        ))
        if self.state == 'empty' and (self.part_is_present(self.key)
                                      and self.part_manager.is_ready()):
            state = 'loaded'
        elif self.state == 'loaded' and self.inspector.state == 'idle':
            try:
                part_info = self.get_part_info(self.key)
                self.test_service.stack_part(
                    part_info,
                    self.part_manager.responsible.key,
                    self.key
                )
                state = 'stacked'
            except Exception as e:  # if problems getting info is because no part
                logger.exception(e)
                state = 'empty'
        elif self.state == 'stacked' and self.inspector.state == 'busy':
            state = 'busy'
            self.current_part = self.inspector.part
        elif self.state == 'busy' and self.inspector.state == 'idle':
            state = self.inspector.test.state if self.inspector.test else 'cancelled'
        elif self.state == 'busy' and self.inspector.state != 'busy':
            logger.info('Inspector state is {}'.format(self.inspector.state))
        elif (self.state in ('success', 'failed', 'cancelled') and
              not self.part_is_present(self.key)):
            state = 'empty'

        if state != self.state:
            self.state = state
            self.part_manager.cavity_state_has_changed(self.key)
            logger.info('State on cavity {} is {}'.format(self.key, state))

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
