import pytest
import cherrypy
import requests
import json
from queue import Queue
from unittest.mock import patch, Mock
from quactrl.services.testing import AuTestResource
# from quactrl.helpers.rest import RestTester  #


class An_AuTestResource:
    def setup_class(cls):
        # Patch runner
        cls._patcher = patch('quactrl.services.testing.AuTestResource.runner')
        cls.runner = cls._patcher.start()
        conf = {'/':{
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True
        }}
        cherrypy.tree.mount(AuTestResource(), '/', conf)
        cls.url = 'http://127.0.0.1:8080'
        cherrypy.engine.start()

    def teardown_class(cls):
        cls._patcher.stop()
        cherrypy.engine.exit()

    def should_return_open_tests(self):
        test = Mock()
        test.part.tracking = '123456789'
        test.part.resource.name = 'part_name'
        test.part.resource.key = 'part_number'
        test.part.resource.description = 'part description'
        test.path.description = 'Control plan description'
        test.path.id = 1234
        test.result = 'iddle'
        test.responsible.key = 'sruiz'

        self.runner.tests = [test, None]

        # Get all tests
        response = requests.get(self.url)

        assert response.status_code == 200
        expected= [
            {
                'status': 'iddle',
                'test_description': 'Control plan description',
                'part': {
                    'tracking': '123456789',
                    'name': 'part_name',
                    'key': 'part_number',
                    'description': 'part description'
                },
                'responsible_key': 'sruiz'
            },
            {
                'status': 'waiting'
            }]
        assert response.json() == expected


        response = requests.get(self.url + '/1')
        assert response.status_code == 200
        assert response.json() == expected[0]

    def should_setup_from_PUT_request(self):
        self.runner.set_location.side_effect = [None, Exception()]

        url = self.url + '/fake'
        response = requests.put(url)

        assert response.status_code == 200
        expected = {'status': 'done',
                    'location': 'fake'}
        assert response.json() == expected

        response = requests.put(self.url + '/invalid')
        assert response.status_code == 500


    def should_begin_test_from_part_information(self):
        json_req = {
            'tracking': '123456789',
            'part_name': 'part_name',
            'responsible_key': 'sruiz',
            'cavity': 1
        }

        response = requests.post(self.url,
                                 json=json_req)

        assert response.status_code == 200

        expected = {
                'status': 'iddle',
                'test_description': 'Control plan description',
                'part': {
                    'tracking': '123456789',
                    'name': 'part_name',
                    'key': 'part_number',
                    'description': 'part description'
                },
                'responsible_key': 'sruiz'
            }
        assert response.json() == expected


    def should_start_ptest_from_part_info(self):
        part_info = {
            'resource_key': 'partnumber',
            'tracking': '123456789',
            'cavity': 1
        }

    def should_stop_any_test(self):
        response = requests.delete(self.url + '/1')
        assert response.status_code == 200
        self.runner.stop.assert_called_with(0)

        response = requests.delete(self.url)
        assert response.status_code == 200
        self.runner.stop.assert_called_with()

    def should_report_events(self):

        self.runner.events = [
            ]

        response = requests.get(self.url + '/events')
        assert response.status_code == 200
        expected = [
            {'signal': 'started',
             'who': {
                 'id': '1',
                 'type': 'Test',
                 'description': 'check description'
             }
            },
            {'signal': 'started',
             'who': {
                 'id': '1.1',
                 'type': 'Check',
                 'description': 'check description'
             }
            },
            {'signal': 'finished',
             'who': {
                 'id': '1.1',
                 'type': 'Check',
                 'description': 'object description',
                 'measures': [],
                 'defects':[],
                 'result': 'ok'

             }
            }
        ]
        assert response.json() == expected
