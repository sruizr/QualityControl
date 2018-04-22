import cherrypy
import json
# from quactrl.domain.testers import TestRunner


# runner = TestRunner()
"""Tester for automatic testing with my tools"""

def echo(request):
    return request.json

@cherrypy.expose
class TestResource:

    def __init__(self,  counter):
        self.counter = counter

    @cherrypy.tools.encode()
    def GET(self):

        return '{"hola":"Salva"}'

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        value = cherrypy.request.json
        self.counter += 1
        value['counter'] = self.counter
        return value

    @cherrypy.popargs('location')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self, location):
        return {'status': 'done', 'location': location}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PATCH(self):
        return echo(cherrypy.request)
