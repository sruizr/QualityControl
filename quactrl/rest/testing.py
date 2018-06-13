import cherrypy
import quactrl.helpers.parse as parse
from quactrl.managers.testing import TestManager


@cherrypy.expose
class AuTestResource:
    runner = TestManager()

    @cherrypy.tools.json_out()
    @cherrypy.popargs('filter')
    def GET(self, filter=None):
        if filter is None:
            json_res = []
            for test in self.runner.tests:
                json_res.append(parse.from_obj(test))
            return json_res
        elif filter == 'events':
            return self._parse_events()
        elif self._is_num(filter):
            index = int(filter) - 1
            test = self.runner.tests[index]
            return parse.from_obj(test)

    def _is_num(self, value):
        try:
            int(value)
            return True
        except ValueError:
            return False

    def _parse_events(self):
        events = self.runner.events
        res = []
        for _ in range(events.qsize()):
            event = events.get()
            res.append(parse.from_obj(event))

        return res

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
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

        self.runner.start_test(part, responsible_key, **test_pars)

        index = int(test_pars.get('cavity', 1)) - 1

        json_res = parse.from_obj(self.runner.tests[index])
        return json_res

    @cherrypy.popargs('location')
    @cherrypy.tools.json_out()
    def PUT(self, location):
        try:
            self.runner.set_location(location)
        except Exception:
            cherrypy.response.status_code = 404
            raise

        return {'status': 'done', 'location': location}


    @cherrypy.popargs('filter')
    @cherrypy.tools.json_out()
    def DELETE(self, filter=None):

        if filter is None:
            pending_parts = self.runner.stop()
        else:
            pending_parts = self.runner.stop(int(filter) - 1)

        return pending_parts
