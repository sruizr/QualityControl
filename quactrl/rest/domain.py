import cherrypy
from quactrl.domain.persistence import dal
import quactrl.rest.parse as parse


@cherrypy.expose
class DomainResource:
    @cherrypy.tools.json_out()
    @cherrypy.popargs('class_name')
    def GET(self, class_name, **kwargs):
        results = dal.get(class_name, **kwargs)

        json_results = []
        for obj in results:
            obj_data = parse.from_obj(obj)
            json_results.append(obj_data)

        if len(json_results) == 1:
            return json_results[0]
        else:
            return json_results

    @cherrypy.tools.json_in()
    def PUT(self):
        """Set connection string for persistence layer"""
        pars = cherrypy.request.json
        success = dal.connect(pars['connection_string'])
        if success:
            cherrypy.response.status = 202
            return
        else:
            cherrypy.response.status = 404

    @cherrypy.popargs('class_name')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, class_name):
        """Create objects on domain"""
        fields = cherrypy.request.json
        obj = dal.create(class_name, **fields)

        if obj is None:
            cherrypy.response.status = 409
        else:
            cherrypy.response.status = 201
            return parse.from_obj(obj)

    @cherrypy.popargs('class_name', 'id')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PATCH(self, class_name, id):
        """Update objects on domain"""

        fields = cherrypy.request.json
        obj = dal.update(class_name, **fields)

        if obj is None:
            cherrypy.response.status = 409
        else:
            cherrypy.response.status = 201
            return parse.from_obj(obj)

    @cherrypy.popargs('class_name', 'id')
    def DELETE(self, class_name, id):
        """Delete objects on domain"""
        success = dal.remove(class_name, id)
        if not success:
            cherrypy.response.status = 409
