import cherrypy
from quactrl.helpers import get_class


class RestServer:
    def __init__(self, host='127.0.0.1', port=8080, config=None):
        if not config:
            self.conf = {
                '/': {
                    'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                    'tools.sessions.on': True,
                    'tools.response_headers.on': True,
                    'tools.response_headers.headers': [
                        ('Content-Type', 'application/json')
                    ]
                }
            }

        self.resources = {}
        self.host = host
        self.port = port

    def add_resource(self, mount_point, resource_name):
        Resource = get_class(resource_name)
        self.resources[mount_point] = Resource()

    def start(self):
        cherrypy.server.socket_host = self.host
        cherrypy.server.socket_port = self.port

        for mounting_point, resource in self.resources.items():
            cherrypy.tree.mount(resource, mounting_point, self.conf)

        cherrypy.engine.start()
        # cherrypy.quickstart(self.resources['/tester'], '/', self.conf )

    def stop(self):
        cherrypy.engine.exit()
