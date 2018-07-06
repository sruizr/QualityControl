import cherrypy
import quactrl.helpers.parsing as parsing
from quactrl.managers.testing import TestManager


@cherrypy.expose
class AuTestResource:
    def __init__(self):
        self.manager = TestManager()

    @cherrypy.tools.json_out()
    @cherrypy.popargs('arg_1', 'arg_2')
    def GET(self, arg_1=None, arg_2=None, last=False):
        """ Retrieve status of testing processes:
        - /events: List all events of all cavities
        - /events/{cavity}: List all events of /cavity/
        - /events/{cavity}?last: List last events since last query
        - /{cavity}: Show test at cavity
        - /: Show all tests on each cavity"""

        if arg_1 is None:  # /
            cavity = 1 if self.manager.cavities == 1 else None
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
            last = last == ''
            return self.handle_get_events(cavity, last)

    def handle_get_events(self, cavity, only_last):
        events = self.manager.load_events(cavity)
        if only_last:
            return parsing.parse(events, 4)
        else:
            if cavity is None:
                return parsing.parse(self.manager.events, 4)
            else:
                return parsing.parse(self.manager.events[cavity - 1], 4)

    def handle_get_tests(self, cavity):

        if cavity is None:
            result = [tester.test for tester in self.manager.testers] \
                     if self.manager.cavities > 1 else \
                     self.manager.testers[0].test
        else:
            result = self.manager.testers[cavity - 1].test
        return parsing.parse(result, 3)

    def _is_num(self, value):
        try:
            int(value)
            return True
        except Exception:
            return False

    # def _parse_events(self, only_last=True):
    #     events = self.manager.events
    #     res = []
    #     for _ in range(events.qsize()):
    #         event = events.get()
    #         res.append(parsing.parse(event))

    #     return res

    @cherrypy.tools.json_in()
    @cherrypy.popargs('cavity')
    def POST(self, cavity=1):
        """Send part for testing
        - /: Send part to tester 1
        - /{cavity}: send part to tester of /cavity/"""
        cavity = int(cavity)
        order = cherrypy.request.json
        part_info, responsible_key, test_pars = order
        self.manager.testers[cavity - 1].start_test(
            part_info, responsible_key, test_pars)

    @cherrypy.popargs('command')
    @cherrypy.tools.json_in()
    def PUT(self, command):
        """Config testing process:
        - /database: Setups database layer
        - /setup: Setups testing process """
        data = cherrypy.request.json
        if command == 'database':
            self.manager.connect(**data)
        elif command == 'setup':
            self.manager.setup(**data)
        else:
            cherrypy.response.status = 404

    @cherrypy.popargs('cavity')
    @cherrypy.tools.json_out()
    def DELETE(self, cavity=None):
        """ Stops testers:
        - /: Stops all testers
        - /{cavity}: Stop tester of cavity /cavity/"""

        if cavity is None:
            if self.manager.cavities == 1:
                pending_orders = self.manager.testers[0].stop()
            else:
                pending_orders = [None] * self.manager.cavities
                for index, tester in enumerate(self.manager.testers):
                    pending_orders[index] = self.manager.testers[index].stop()
        else:
            cavity = int(cavity)
            pending_orders = self.manager.testers[cavity - 1].stop()

        return pending_orders
