import cherrypy
import quactrl.helpers.parse as parse
from quactrl.managers.crud import Crud


@cherrypy.expose
class CrudResource:
    """Simple crud interface"""
    def __init__(self):
        self.manager = Crud()

    @cherrypy.tools.json_out()
    @cherrypy.popargs('class_name')
    def GET(self, class_name, **kwargs):
        results = self.manager.read(class_name, **kwargs)

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
        success = self.manager.connect(pars['connection_string'])
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
        obj = self.manager.create(class_name, **fields)

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
        obj = self.manager.update(class_name, int(id), **fields)

        if obj is None:
            cherrypy.response.status = 409
        else:
            cherrypy.response.status = 201
            return parse.from_obj(obj)

    @cherrypy.popargs('class_name', 'id')
    def DELETE(self, class_name, id):
        """Delete objects on domain"""
        id = int(id)
        success = self.manager.delete(class_name, id)
        if not success:
            cherrypy.response.status = 409
