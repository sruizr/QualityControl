import time
import threading


class SetupException(Exception):
    pass


class MonoLauncher(threading.Thread):
    """Launcher for a tool with only one cavity
    """
    def __init__(self, service, presence_input, refresh_time):
        super().__init__()
        self.service = service
        self.data = service.db
        self.presence_input = presence_input
        self.refresh_time = refresh_time

        self._continue = True
        self.setDaemon(True)

        self.cavity_states = {}
        self.responsible = None

    def run(self):
        while self._continue:
            if self.is_ready():
                self._update_cavities()
            time.sleep(self.refresh_time)


class MultiLauncher(threading.Thread):
    """Launcher for a tool with multiple cavities
    """
    def __init__(self, service, presence_input, refresh_time):
        super().__init__()
        self.service = service
        self.data = service.db
        self.presence_input = presence_input
        self.refresh_time = refresh_time

        self._continue = True
        self.setDaemon(True)

        self.cavity_states = {}
        self.responsible = None

    def run(self):
        while self._continue:
            if self.is_ready():
                self._update_cavities()
            time.sleep(self.refresh_time)

    @property
    def dev_container(self):
        return self.service.dev_container

    @property
    def inspectors(self):
        return self.service.inspectors

    @property
    def active_cavities(self):
        return self.service.active_cavities

    def set_responsible(self, key):
        if key is None:
            self.responsible = None
        else:
            self.responsible = self.data.Persons().get(key)

    def get_events(self, cavity=None):
        return self.service.get_events(cavity)

    def get_last_events(self, cavity=None):
        return self.service.get_last_events(cavity)

    def get_responsible(self):
        return self.responsible

    def start_inspector(self, cavity=None):
        self.service.start_inspector(cavity)

    def is_ready(self):
        """Is the system ready to load parts on cavities
        """
        return self.responsible is not None

    def get_part_info(self, cavity):
        """Retrieve part_number and serial number for a loaded cavity
        """
        raise NotImplementedError()

    def update_cavity(self, cavity, state):
        """Update view of cavity
        """
        raise NotImplementedError()

    def _update_cavities(self):
        self.refresh_states()
        for cavity, state in self.cavity_states.items():
            if state == 'loaded':
                part_info = self.get_part_info(cavity)
                responsible = self.responsible.key
                self.service.stack_part(part_info, responsible, cavity)
                self.cavity_states[cavity] == 'stacked'

    def _get_inspector_state(self, cavity):
        inspector = self.service.inspectors[cavity]
        if inspector.state == 'waiting':
            if inspector.test:
                return inspector.test.state
            else:
                return 'empty'
        elif inspector.state == 'iddle':
            return 'iddle'

    def refresh_states(self):
        self.presence_input.read()
        for cavity in self.service.active_cavities:
            last_state = self.cavity_states.get(cavity)
            inspector_state = self._get_inspector_state(cavity)
            state = inspector_state
            if last_state in ('success', 'failed', 'cancelled'):
                if not self.presence_input(cavity):
                    state = 'empty'
            elif last_state == 'empty':
                if self.presence_input(cavity):
                    state = 'loaded'
            if state != last_state:
                self.update_cavity(cavity, state)
                self.cavity_states[cavity] = state

    def stop(self):
        """Stops iteration
        """
        self._continue = False
        self.join()

    def __del__(self):
        self.stop()
