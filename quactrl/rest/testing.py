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

    def parse_event(self, event):
        event_data = {
            'signal': event.signal,
            'obj': self.parse(event.obj)}
        if hasattr(event, 'pars'):
            event_data['pars'] = event.pars

        return event_data

    def parse_test(self, test, **fields):
        if test is None:
            test_data = {'status': 'waiting'}
        else:
            test_data = {
                'status': test.status,
                'test_description': test.path.description,
                'responsible_key': test.responsible.key,
                'part': self.parse_part(test.part)
            }

        for key, value in fields.items():
            test_data[key] = value

        test_data['type'] = 'Test'
        return test_data

    def parse_check(self, check, id=None):
        check_data = {
            'description': check.path.description.capitalize(),
            'measures': [self.parse(measure) for measure in check.measures],
            'defects': [self.parse(defect) for defect in check.defects],
            'result': check.result,
        }

        if id is not None:
            check_data['id'] = str(id)

        check_data['type'] = 'Check'
        return check_data

    def parse_part(self, part):
        return {
            'type': 'Part',
            'tracking': part.tracking,
            'key': part.resource.key,
            'name': part.resource.name,
            'description': part.resource.description
        }

    def parse_measure(self, measure):
        data = {'type': 'Measure',
                'characteristic': self.parse(measure.characteristic),
                'value': measure.qty
                }
        return data

    def parse_characteristic(self, char):
        return {'type': 'Characteristic',
                'description': char.description.capitalize(),
                'key': char.key
                }

    def parse_defect(self, defect):
        return {'type': 'Defect',
                'description': defect.description.capitalize(),
                'char_key': defect.characteristic.key
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
        data = cherrypy.request.json
        part = {}
        responsible_key = None
        test_pars = {}
        for key, value in data.items():
            if key.startswith('part_') or key=='tracking':
                part[key] = value
            elif key=='responsible_key':
                responsible_key = value
            else:
                test_pars[key] = value

        self.runner.start_test(part, responsible_key, **test_pars)

        index = int(test_pars.get('cavity', 1)) - 1

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
