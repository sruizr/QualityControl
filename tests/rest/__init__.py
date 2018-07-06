import cherrypy
from unittest.mock import patch


class TestResource:
    """Framework for testing API Rest Resources"""
    @classmethod
    def setup_class(cls, Resource):
        cls.Resource = Resource

    def setup_method(self, method):
        conf = {'/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True
        }}
        self.resource = self.Resource()
        cherrypy.tree.mount(self.resource, '/', conf)
        self.url = 'http://127.0.0.1:8080'
        cherrypy.engine.start()

    def create_patches(self, definitions):
        self.patch = {}
        self._patchers = []
        for definition in definitions:
            patcher = patch(definition)
            name = definition.split('.')[-1]
            self.patch[name] = patcher.start()
            self._patchers.append(patcher)
            setattr(self, name, self.patch[name])

    def teardown_method(self, method):
        cherrypy.engine.exit()
