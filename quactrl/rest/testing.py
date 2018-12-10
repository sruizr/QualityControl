import cherrypy
import os
from quactrl.rest.parsing import parse
from quactrl.helpers import is_num


def try_int(cavity):
    if is_num(cavity):
        return int(cavity)


@cherrypy.expose
class Resource:
    def __init__(self, service):
        """Resource avalaible with API REST and CORS security solved
        """
        self.service = service

    def OPTIONS(self, key, word):
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Access-Control-Allow-Origin'

        possible_methods = ('PUT', 'DELETE', 'PATCH')
        methods =[http_method for http_method in possible_methods
                  if hasattr(self, http_method)]
        cherrypy.response.headers['Access-Control-Allow-Methods'] = ','.join(methods)


class CavitiesResource(Resource):
    @cherrypy.tools.json_out()
    def GET(self, key=None):
        if is_num(key):
            return parse(self.service.inspectors[int(key)])
        elif key is None:
            if key in self.service.active_cavities:
                return parse(self.service.inspectors[None])
            else:
                return {
                    cavity: parse(self.service.inspectors[cavity])
                    for cavity in self.service.active_cavities
                }
        else:
            cherrypy.response.status = 400

    def PUT(self, key=None):
        """Active cavity by key
        """
        if is_num(key):
            self.service.start_inspector(int(key))
        elif key is None:
            self.service.start_inspector()
        else:
            cherrypy.response.status = 400

    @cherrypy.tools.json_out()
    def DELETE(self, key=None):
        """Deactive cavity by key, all if None
        """
        if is_num(key):
            return self.service.stop_inspector(int(key))
        elif key is None:
            return self.service.stop_inspector()
        else:
            cherrypy.response.status = 400


class PartModelResource(Resource):
    @cherrypy.tools.json_out()
    def GET(self):
        try:
            return parse(self.service.part_model)
        except:
            cherrypy.response.status = 404

    def PUT(self, key):
        try:
            self.service.set_part_model(key)
        except:
            cherrypy.response.status = 404


class BatchResource(Resource):
    def PUT(self, key):
        try:
            self.service.set_batch(key)
        except ValueError:
            cherrypy.response.status = 400

    @cherrypy.tools.json_out()
    def GET(self):
        output = {'class': 'Batch',
                  'batch_number': self.service.batch_number}
        return output


class PartResource(Resource):
    @cherrypy.tools.json_out()
    def GET(self, cavity):
        if is_num(cavity):
            cavity = int(cavity)
            return parse(self.service.get_part(cavity))

    @cherrypy.tools.json_in()
    def POST(self, cavity):
        pass


class EventsResource(Resource):
    @cherrypy.tools.json_out()
    def GET(self, cavity=None, word=None):
        get = self.service.get_events
        if cavity == 'last' or word == 'last':
            get = self.service.get_last_events

        cavity = int(cavity) if is_num(cavity) else None
        events = get(cavity)
        return self._parse_events(events)

    def _parse_events(self, events):
        if events is dict:
            result = {cavity: self._parse_events(cav_events)
                      for cavity, cav_events in events}
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
    def GET(self, key):
        return parse(self.service.responsible)

    def PUT(self, key):
        try:
            self.service.set_responsible(key)
        except:
            cherrypy.NotFound()

    def DELETE(self):
        self.service.set_responsible(None)


_RESOURCES = {
    'events': EventsResource,
    'cavities': CavitiesResource,
    'part': PartResource,
    'part_model': PartModelResource,
    'batch': BatchResource
}



class RootResource(Resource):
    def __init__(self, service, resources):
        super().__init__(service)
        for resource in resources:
            setattr(self, resource, _RESOURCES[resource](service))

    @cherrypy.tools.json_in()
    def PUT(self, cavity=None):
        dyncir = self.service.dev_container.dyncir()
        kwargs = cherrypy.response.json()
        voltage = int(kwargs.get('voltage', 230))

        dyncir.swicth_on_dut(cavity=try_int(cavity), voltage=voltage)

    def DELETE(self, cavity=None):

        self.service.stop()
        os.system('shutdown now')
        cherrypy.response.status = 501
