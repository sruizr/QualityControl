import cherrypy
from unittest.mock import patch, Mock


class TestResource:
    """Framework for testing API Rest Resources"""
    @classmethod
    def setup_class(cls, Resource, *args):
        cls.Resource = Resource

        conf = {'/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True
        }}
        cls.resource = Resource(Mock(), *args)
        cherrypy.tree.mount(cls.resource, '/', conf)
        cls.url = 'http://127.0.0.1:8080'
        cherrypy.engine.start()

    def create_patches(self, definitions):
        self.patch = {}
        self._patchers = []
        for definition in definitions:
            patcher = patch(definition, autospec=True)
            name = definition.split('.')[-1]
            self.patch[name] = patcher.start()
            self._patchers.append(patcher)
            setattr(self, name, self.patch[name])

    def teardown_method(self, method):
        for patcher in self._patchers:
            patcher.stop()

    def teardown_class(cls):
        cherrypy.engine.exit()
