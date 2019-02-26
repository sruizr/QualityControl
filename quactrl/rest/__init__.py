import cherrypy


class Server:
    def __init__(self, root_resource, host='127.0.0.1', port=8080,
                 config=None):
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

        self.host = host
        self.port = port
        cherrypy.tree.mount(root_resource, '/', self.conf)

    def start(self, silent_access=False):
        cherrypy.server.socket_host = self.host
        cherrypy.server.socket_port = self.port
        # propagate = True...
        cherrypy.config.update({'log.screen': not silent_access})

        cherrypy.engine.start()

    def stop(self):
        cherrypy.engine.exit()
