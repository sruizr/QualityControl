import cherrypy
import quactrl.helpers.parsing as parsing
from quactrl.managers.testing import TestManager


@cherrypy.expose
class AuTestResource:
    def __init__(self):
        self.manager = TestManager()

    @cherrypy.tools.json_out()
    @cherrypy.popargs('arg_1', 'arg_2')
    def GET(self, arg_1=None, arg_2=None, command=None):
        """ Retrieve status of testing processes:
        - /events: List all events of all cavities
        - /events/{cavity}: List all events of /cavity/
        - /events/{cavity}?last: List last events since last query
        - /{cavity}: Show state of test at cavity 1
        - /: Show state of all tests"""

        if arg_1 is None:  # /
            cavity = 1 if self.managers.cavities == 1 else None
            return self.handle_get_tests(cavity)
        elif self._is_num(arg_1):  # /{cavity}
            cavity = int(arg_1)
            return self.handle_get_tests(cavity)
        elif arg_1 == 'events':
            cavity = None
            if arg_2 is None and self.manager.cavities == 1:
                cavity = 1
            elif self._is_num(arg_2):
                cavity = int(arg_2)
            only_last = command == 'last'
            return self.handle_get_events(cavity, only_last)

    def handle_get_events(self, cavity, only_last):
        events = self.manager.load_events(cavity)
        if only_last:
            return parsing.parse(events)
        else:
            if cavity is None:
                return parsing.parse(events, 4)
            else:
                return parsing.parse(self.manager.events[cavity], 4)

    def handle_get_tests(self, cavity):
        result = self.manager.tests if self.manager.cavities > 1 \
                 else self.manager.tests[0]
        return parsing.parse(result, 4)

    def _is_num(self, value):
        try:
            int(value)
            return True
        except ValueError:
            return False

    def _parse_events(self, only_last=True):
        events = self.manager.events
        res = []
        for _ in range(events.qsize()):
            event = events.get()
            res.append(parsing.parse(event))

        return res

    @cherrypy.tools.json_in()
    @cherrypy.popargs('cavity')
    def POST(self, cavity=1):
        """Send part for testing
        - /: Send part to tester 1
        - /{cavity}: send part to tester of /cavity/"""

        order = cherrypy.request.json

        part_info, responsible_key, test_pars = order

        self.manager.tester[cavity - 1].start_test(part, responsible_key, test_pars)

    @cherrypy.popargs('command')
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def PUT(self, command):
        """Config testing process:
        - /database: Setups database layer
        - /setup: Setups testing process """
        data = cherrypy.request.json
        try:
            if command == 'database':
                answer = self.manager.connect(data)
            elif command == 'setup':
                answer = self.manager.setup(data)
        except Exception:
            cherrypy.response.status_code = 404
            raise
        return answer

    @cherrypy.popargs('filter')
    @cherrypy.tools.json_out()
    def DELETE(self, filter=None):
        """ Stops testers:
        - /: Stops all testers
        - /{cavity}: Stop tester of cavity /cavity/"""

        if filter is None:
            pending_orders = self.manager.stop()
        else:
            pending_orders  = self.manager.stop(int(filter) - 1)

        return pending_orders

    def _parse_event(self, event):
        pass
