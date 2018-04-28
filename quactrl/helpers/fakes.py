from http.server import BaseHTTPRequestHandler, HTTPServer
import json


routes = {
    'GET': {
        '/tests/1/parts': {
            'key': '12364', 'description': 'CamRegis'
        }

    }
}


class RequestHandler(BaseHTTPRequestHandler):
    routes = {}

    def do_GET(self):
        # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type','application/json')
        self.end_headers()

        routes = self.routes['GET']
        if self.path in routes.keys():
            out = routes[self.path]
        else:
            out = {}

        # Send message back to client
        out = json.dumps(out)
        # Write content as utf-8 data
        self.wfile.write(bytes(out, "utf8"))

        return


    def do_PUT(self):
                # Send response status code
        self.send_response(200)

        # Send headers
        self.send_header('Content-type','application/json')
        self.end_headers()

        # Send message back to client
        out  = {'put': [1, 12]}
        out = json.dumps(out)
        # Write content as utf-8 data
        self.wfile.write(bytes(out, "utf8"))

        return

    def do_PATCH(self):
        self.send_response(200)

        # Send headers
        self.send_header('Content-type','application/json')
        self.end_headers()

        # Send message back to client
        out  = {'patch': [1, 12]}
        out = json.dumps(out)
        # Write content as utf-8 data
        self.wfile.write(bytes(out, "utf8"))

        return


def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ('127.0.0.3', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


print("Haciendo")
RequestHandler.routes = routes
run(handler_class=RequestHandler)
