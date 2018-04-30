import cherrypy
import json
from quactrl.domain.check import TestRunner



def echo(request):
    return request.json

class Parser:
    """Parse domain objects to dicts"""

    def parse(self, obj):
        types = {

    def _parse_event(self, event):


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
                json_res.append(self._parse_test(test))
            return json_res
        elif filter == 'events':
            return self._parse_events()
        elif self._is_num(filter):
            index = int(filter) - 1
            test = self.runner.tests[index]
            return self._parse_test(test)

    def _is_num(self, value):
        try:
            int(value)
            return True
        except:
            return False

    def _parse_events(self):

        events = self.runner.events
        res = []
        for _ in range(events.qsize()):
            event = events.get()
            res.append(self._parse(event))
        return res

    def _parse_event(self, event):
        event_data = {
            'signal': event.signal,
            'who': self._parse(event.who)}
        return event_data

    def _parse_test(self, test):
        if test is None:
            test_res ={'status': 'waiting'}
        else:
            test_res = {
                'status': 'iddle',
                'test_description': test.path.description,
                'responsible_key': test.responsible.key,
                'part': {
                    'tracking': test.part.tracking,
                    'key': test.part.resource.key,
                    'name': test.part.resource.name,
                    'description': test.part.resource.description
                }
            }
        return test_res

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        part_info = cherrypy.request.json

        self.runner.begin_test(**part_info)
        index = int(part_info.get('cavity', 1)) - 1

        json_res = self._parse_test(self.runner.tests[index])
        return json_res

    @cherrypy.popargs('location')
    @cherrypy.tools.json_out()
    def PUT(self, location):
        try:
            self.runner.set_location(location)
        except:
            cherrypy.response.status_code = 404
            raise

        return {'status': 'done', 'location': location}

    @cherrypy.popargs('filter')
    def DELETE(self, filter=None):
        if filter is None:
            pending_parts = self.runner.stop()
        else:
            pending_parts = self.runner.stop(int(filter) - 1)

        return pending_parts

    def _parse(self, obj):
        types = {
            'Test': self._parse_test,
            'Check': self._parse_check,
            'Part': self._parse_part,
            'Event': self._parse_event
        }
        return types[obj.__class__.__name__](obj)
