from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import copy


class MockRestHandler(BaseHTTPRequestHandler):
    routes = None

    def do_GET(self):
        self._handle_path('GET')

    def do_PUT(self):
        self._handle_path('PUT')

    def do_PATCH(self):
        self._handle_path('PATCH')

    def do_DELETE(self):
        self._handle_path('DELETE')

    def do_POST(self):
        self._handle_path('POST')

    def _handle_path(self, method):
        routes = self.routes[method]
        if self.path in routes.keys():
            answer = routes[self.path]
            if type(answer) is dict and 'many' in answer.keys():
                answers = answer['many']
                requests = answer.get('requests', 0)
                index = requests % len(answers)
                answer = answers[index]
            answer = copy.deepcopy(answer)
            status_code = answer.pop('status_code', 200)
            self._handle_res(status_code, answer)
        else:
            self._handle_res(404, {'error_at': method + ':' + self.path})

    def _handle_res(self, status_code, json_data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        # Send message back to client
        out = json.dumps(json_data)
        # Write content as utf-8 data
        self.wfile.write(bytes(out, "utf8"))

        return

class Server:
    def __init__(self, host='127.0.0.1', port=8000):
        self.server_address = (host, port)

    def start(self, handler_class):
        self.httpd = HTTPServer(server_address, handler_class)
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()
