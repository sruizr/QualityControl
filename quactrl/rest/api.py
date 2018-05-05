#
import cherrypy
from .autester import TestResource


class App:
    def __init__(self, config=None):
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

        self.counter = 0
        self.resources = {'/tester': TestResource(self.counter)}

    def run(self):
        for mounting_point, resource in self.resources.items():
            cherrypy.tree.mount(resource, mounting_point, self.conf)

        cherrypy.engine.start()
        # cherrypy.quickstart(self.resources['/tester'], '/', self.conf )

    def stop(self):
        cherrypy.engine.exit()
