import cherrypy
from quactrl.domain.check import TestRunner



def echo(request):
    return request.json

class Parser:
    """Parse domain objects to dicts"""

    def parse(self, obj, **fields):
        class_name = obj.__class__.__name__
        method_name = 'parse_{}'.format(class_name.lower())
        method = getattr(self, method_name)
        return method(obj, **fields)

    def parse_event(self, event, **fields):
        event_data = {
            'signal': event.signal,
            'who': self._parse(event.who)}
        return event_data

    def parse_test(self, test, **fields):
        if test is None:
            test_res ={'status': 'waiting'}
        else:
            test_res = {
                'status': 'iddle',
                'test_description': test.path.description,
                'responsible_key': test.responsible.key,
                'part': self.parse_part(test.part)
            }

        if id is not None:
            test_res['id'] = str(id)

        return test_res

    def parse_check(self, check, id=None):
        check_data = {
        }

        if id is not None:
            check_data['id'] = str(id)

        return check_data

    def parse_part(self, part):
        return {
            'tracking': part.tracking,
            'key': part.resource.key,
            'name': part.resource.name,
            'description': part.resource.description
        }


@cherrypy.expose
class AuTestResource:
    runner = TestRunner()
    parser = Parser()

    @cherrypy.tools.json_out()
    @cherrypy.popargs('filter')
    def GET(self, filter=None):
        if filter is None:
            json_res = []
            for test in self.runner.tests:
                json_res.append(self.parser.parse(test))
            return json_res
        elif filter == 'events':
            return self._parse_events()
        elif self._is_num(filter):
            index = int(filter) - 1
            test = self.runner.tests[index]
            return self.parser.parse(test)

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
            res.append(self.parser.parse(event))

        return res

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        part_info = cherrypy.request.json

        self.runner.begin_test(**part_info)
        index = int(part_info.get('cavity', 1)) - 1

        json_res = self.parser.parse(self.runner.tests[index])
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
    def DELETE(self, filter=None):
        if filter is None:
            pending_parts = self.runner.stop()
        else:
            pending_parts = self.runner.stop(int(filter) - 1)

        return [self.parser.parse(part) for part in pending_parts]
