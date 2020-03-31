import cherrypy
import logging
from .resources import RootResource


class Server:
    def __init__(self, part_manager, host='127.0.0.1', port=8080,
                 resources=None, config=None):
        if not config:
            self.conf = {
                '/': {
                    'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                    'tools.sessions.on': True,
                    'tools.response_headers.on': True,
                    'tools.response_headers.headers': [
                        ('Access-Control-Allow-Headers', 'Origin, Content-Type'),
                        ('access-Control-Allow-Origin', '*')
                    ]
                }
            }

        if not resources:
            resources = ['events', 'cavities', 'part_model', 'batch',
                         'responsible', 'part']

        root_resource = RootResource(part_manager, resources)
        self.host = host
        self.port = port
        cherrypy.tree.mount(root_resource, '/', self.conf)

    def start(self, silent_access=True):
        logging.getLogger('cherrypy').propagate = False

        cherrypy.server.socket_host = self.host
        cherrypy.server.socket_port = self.port
        cherrypy.config.update({'log.screen': not silent_access})
        cherrypy.engine.start()

    def stop(self):
        cherrypy.engine.exit()
