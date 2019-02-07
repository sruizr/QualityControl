import os
import datetime
import cherrypy
from quactrl.rest.parsing import parse
from quactrl.helpers import is_num


def try_int(cavity):
    if is_num(cavity):
        return int(cavity)


@cherrypy.expose
class Resource:
    def __init__(self, part_manager):
        """Resource avalaible with API REST and CORS security solved
        """
        self.part_manager = part_manager

    def OPTIONS(self, key=None, word=None):
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Access-Control-Allow-Origin'
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        possible_methods = ('PUT', 'DELETE', 'PATCH')
        methods = [http_method for http_method in possible_methods
                   if hasattr(self, http_method)]
        cherrypy.response.headers['Access-Control-Allow-Methods'] = ','.join(methods)


class CavitiesResource(Resource):
    @cherrypy.tools.json_out()
    def GET(self, key=None):
        key = try_int(key)
        if key in self.part_manager.cavities:
            return parse(self.part_manager.cavities[key])
        else:
            return {
                key: parse(cavity)
                for key, cavity in self.part_manager.cavities.items()
            }

    def PUT(self, key=None):
        """Active cavity by key
        """
        key = try_int(key)
        self.part_manager.add_cavity(key)

    @cherrypy.tools.json_in()
    def POST(self, key=None):
        """Returns answer to question if there is
        """
        key = try_int(key)
        inspector = self.part_manager.test_service.inspectors[key]

        kwargs = cherrypy.request.json
        inspector.test.answer(**kwargs)

    @cherrypy.tools.json_out()
    def DELETE(self, key=None):
        """Deactive cavity by key, all if None
        """
        key = try_int(key)
        try:
            self.part_manager.remove_cavity(key)
        except Exception as e:
            cherrypy.response.status = 400
            cherrypy.response.body = str(e)


class PartModelResource(Resource):
    @cherrypy.tools.json_out()
    def GET(self):
        return parse(self.part_manager.part_model)

    def PUT(self, key):
        self.part_manager.set_part_model(key)


class BatchResource(Resource):
    def PUT(self, key):
        try:
            self.part_manager.set_batch(key)
        except ValueError:
            cherrypy.response.status = 400

    @cherrypy.tools.json_out()
    def GET(self):
        output = {'class': 'Batch',
                  'batch_number': self.part_manager.batch_number}
        return output


class PartResource(Resource):
    @cherrypy.tools.json_out()
    def GET(self, cavity):
        key = try_int(cavity)
        return parse(self.part_manager.cavities[key].part)

    @cherrypy.tools.json_in()
    def POST(self, cavity):
        pass



class EventsResource(Resource):
    @cherrypy.tools.json_out()
    def GET(self, cavity=None, word=None):
        service = self.part_manager.test_service
        get_events = service.get_events
        if cavity == 'last' or word == 'last':
            get_events = service.get_last_events
        key = try_int(cavity)
        events = get_events(key)

        return self._parse_events(events)

    def _parse_events(self, events):
        if type(events) is dict:
            result = {cavity: self._parse_events(cav_events)
                      for cavity, cav_events in events.items()}
        else:
            result = []
            for event in events:
                if event[0] not in ('done', 'walking', 'walked'):
                    event_dict = {'state': event[0],
                                  'obj': parse(event[1])}
                    if len(event) > 2:  # Event is an exception
                        event_dict['trace'] = '/n'.join(event[2])
                    result.append(event_dict)
        return result


class ResponsibleResource(Resource):
    @cherrypy.tools.json_out()
    def GET(self):
        return parse(self.part_manager.responsible)

    def PUT(self, key):
        try:
            self.part_manager.set_responsible(key)
        except ValueError:
            cherrypy.NotFound()

    def DELETE(self):
        self.part_manager.set_responsible(None)


_RESOURCES = {
    'events': EventsResource,
    'cavities': CavitiesResource,
    'part': PartResource,
    'part_model': PartModelResource,
    'batch': BatchResource,
    'responsible': ResponsibleResource
}


@cherrypy.expose
class Time:
    @cherrypy.tools.json_out()
    def GET(self):
        return {'now': datetime.datetime.now().isoformat()}


class RootResource(Resource):
    def __init__(self, part_manager, resources):
        super().__init__(part_manager)
        self.time = Time()
        for resource in resources:
            setattr(self, resource, _RESOURCES[resource](part_manager))

    @cherrypy.tools.json_in()
    def PUT(self, cavity=None):
        dyncir = self.part_manager.test_service.dev_container.dyncir()
        kwargs = cherrypy.request.json
        voltage = int(kwargs.get('voltage', 230))

        dyncir.switch_on_dut(cavity=try_int(cavity), voltage=voltage)

    def DELETE(self, cavity=None):
        self.part_manager.stop()
        os.system('shutdown now')
        cherrypy.response.status = 501
