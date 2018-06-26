import cherrypy
import quactrl.helpers.parsing as parsing
from quactrl.managers.testing import TestManager


@cherrypy.expose
class AuTestResource:
    def __init__(self):
        self.manager = TestManager()

    @cherrypy.tools.json_out()
    @cherrypy.popargs('filter')
    def GET(self, filter=None):
        """ Retrieve status of testing processes:
        - /events: List all events of all cavities
        - /events/last: List last events since last query
        - /{cavity}: Show state of tester
        - /: Show state of all testers"""

        if filter is None:
            json_res = []
            for test in self.manager.tests:
                json_res.append(parsing.parse(test))
            return json_res
        elif filter == 'events':
            return self._parse_events()
        elif self._is_num(filter):
            index = int(filter) - 1
            test = self.manager.tests[index]
            return parsing.parse(test)

    def _is_num(self, value):
        try:
            int(value)
            return True
        except ValueError:
            return False

    def _parse_events(self):
        events = self.manager.events
        res = []
        for _ in range(events.qsize()):
            event = events.get()
            res.append(parsing.parse(event))

        return res

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        """Send part for testing
        - /: Send part to tester 1
        - /{cavity}: send part to tester of /cavity/"""

        data = cherrypy.request.json
        part = {}
        responsible_key = None
        test_pars = {}
        for key, value in data.items():
            if key.startswith('part_') or key == 'tracking':
                part[key] = value
            elif key == 'responsible_key':
                responsible_key = value
            else:
                test_pars[key] = value

        self.manager.start_test(part, responsible_key, **test_pars)

        index = int(test_pars.get('cavity', 1)) - 1

        json_res = parsing.parse(self.manager.tests[index])
        return json_res

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
            pending_parts = self.manager.stop()
        else:
            pending_parts = self.manager.stop(int(filter) - 1)

        return pending_parts


    def _parse_event(self, event):
        pass
