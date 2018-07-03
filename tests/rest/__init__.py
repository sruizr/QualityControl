import cherrypy
from unittest.mock import patch


class TestResource:
    @classmethod
    def setup_class(cls, Resource):
        conf = {'/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True
        }}
        cls.resource = Resource()
        cherrypy.tree.mount(cls.resource, '/', conf)
        cls.url = 'http://127.0.0.1:8080'
        cherrypy.engine.start()

    @classmethod
    def create_patches(cls, definitions):
        cls.patch = {}
        cls._patchers = []
        for definition in definitions:
            patcher = patch(definition)
            name = definition.split('.')[-1]
            cls.patch[name] = patcher.start()
            cls._patchers.append(patcher)
            setattr(cls, name, cls.patch[name])

    @classmethod
    def teardown_class(cls):
        for patcher in cls._patchers:
            patcher.stop()
        cherrypy.engine.exit()
