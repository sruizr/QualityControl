import cherrypy
from quactrl.rest.testing import RootResource as TestResource


class TestServer:
    def __init__(self, service, resources, host='127.0.0.1', port=8080, config=None):
        if not config:
            self.conf = {
                '/': {
                    'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                    'tools.sessions.on': True,
                    'tools.response_headers.on': True,
                    'tools.response_headers.headers': [
                        ('Content-Type', 'application/json'),
                        ('Access-Control-Allow-Origin', '*')
                    ]
                }
            }

        self.host = host
        self.port = port
        resource = TestResource(service, resources)
        cherrypy.tree.mount(resource, '/', self.conf)

    def start(self):
        cherrypy.server.socket_host = self.host
        cherrypy.server.socket_port = self.port

        cherrypy.engine.start()
        # cherrypy.quickstart(self.resources['/tester'], '/', self.conf )

    def stop(self):
        cherrypy.engine.exit()
