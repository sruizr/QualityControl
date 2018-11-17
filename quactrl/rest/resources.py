import cherrypy
from quactrl.rest.parsing import parse


@cherrypy.expose
class Resource:
    def __init__(self, service):
        """Resource avalaible with API REST
        """
        self.service = service

    def OPTIONS(self, key, word):
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Access-Control-Allow-Origin'
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'PUT,DELETE'


class CavitiesResource(Resource):
    @cherrypy.tools.json_out()
    def GET(self, key=None):
        return parse(self.service.inspectors[key])

    def PUT(self, key):
        """Active cavity by key
        """
        pass

    def DELETE(self, key=None):
        """Deactive cavity by key, all if None
        """
        pass


class PartModelResource(Resource):
    def GET(self):
        return

    def PUT(self, key):
        try:
            self.service.set_part_model(key)
        except:
            cherrypy.response.status = 404

class Batch(Resource):
    pass


class PartResouce(Resource):
    pass


class EventsResource(Resource):
    def GET(self, key=None, word=None):
        pass



class ResponsibleResource(Resource):
    def PUT(self, key):
        try:
            self.service.set_responsible(key)
        except:
            cherrypy.
    def DELETE(self):
        self.service.set_responsible(None)

    @cherrypy.tools.json_out()
    def GET(self, key):
        return parse(self.service.responsible)
