import pytest
import cherrypy
import requests
from queue import Queue
from unittest.mock import patch, Mock
from quactrl.services.testing import AuTestResource, Parser
# from quactrl.helpers.rest import RestTester  #


class A_Patcher:

    def should_select_suitable_method_from_class_name(self):
        self.parser = Parser()
        mock = Mock()
        self.parser.parse_mock = Mock()

        self.parser.parse(mock)

        self.parser.parse_mock.assert_called_with(mock)

    def should_parse_test(self):
        self.parser = Parser()
        test = Mock()
        test.__class__.__name__ = 'Test'
        test.part.tracking = '123456789'
        test.part.resource.name = 'part_name'
        test.part.resource.key = 'part_number'
        test.part.resource.description = 'part description'
        test.path.description = 'Control plan description'
        test.path.id = 1234
        test.result = 'iddle'
        test.responsible.key = 'sruiz'

        result = self.parser.parse(test)

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
        assert result == expected


class An_AuTestResource:
    def setup_class(cls):
        # Patch runner
        cls._runner_patcher = patch(
            'quactrl.services.testing.AuTestResource.runner'
        )
        cls._parser_patcher = patch(
            'quactrl.services.testing.AuTestResource.parser')

        cls.runner = cls._runner_patcher.start()
        cls.parser = cls._parser_patcher.start()
        conf = {'/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True
        }}
        cherrypy.tree.mount(AuTestResource(), '/', conf)
        cls.url = 'http://127.0.0.1:8080'
        import pdb; pdb.set_trace()
        cherrypy.engine.start()

    def teardown_class(cls):
        cls._runner_patcher.stop()
        cls._parser_patcher.stop()
        cherrypy.engine.exit()

    def setup_method(self, method):
        self.parser.parse = lambda obj: {'key': obj.key}

    @pytest.mark.current
    def should_return_open_tests(self):
        self.runner.tests = [Mock(key='test_{}'.format(_n))
                             for _n in range(2)]

        # Get all tests
        response = requests.get(self.url)

        assert response.status_code == 200
        expected= [
            {'key': 'test_0'},
            {'key': 'test_1'}]
        assert response.json() == expected

        response = requests.get(self.url + '/1')
        assert response.status_code == 200
        assert response.json() == expected[0]

    # def should_setup_from_PUT_request(self):
    #     self.runner.set_location.side_effect = [None, Exception()]

    #     url = self.url + '/fake'
    #     response = requests.put(url)

    #     assert response.status_code == 200
    #     expected = {'status': 'done',
    #                 'location': 'fake'}
    #     assert response.json() == expected

    #     response = requests.put(self.url + '/invalid')
    #     assert response.status_code == 500


    # def should_begin_test_from_part_information(self):
    #     json_req = {
    #         'tracking': '123456789',
    #         'part_name': 'part_name',
    #         'responsible_key': 'sruiz',
    #         'cavity': 1
    #     }

    #     response = requests.post(self.url,
    #                              json=json_req)

    #     assert response.status_code == 200

    #     expected = {
    #             'status': 'iddle',
    #             'test_description': 'Control plan description',
    #             'part': {
    #                 'tracking': '123456789',
    #                 'name': 'part_name',
    #                 'key': 'part_number',
    #                 'description': 'part description'
    #             },
    #             'responsible_key': 'sruiz'
    #         }
    #     assert response.json() == expected


    # def should_start_ptest_from_part_info(self):
    #     part_info = {
    #         'resource_key': 'partnumber',
    #         'tracking': '123456789',
    #         'cavity': 1
    #     }

    # def should_stop_any_test(self):
    #     response = requests.delete(self.url + '/1')
    #     assert response.status_code == 200
    #     self.runner.stop.assert_called_with(0)

    #     response = requests.delete(self.url)
    #     assert response.status_code == 200
    #     self.
    #    runner.stop.assert_called_with()

    # def should_report_events(self):
    #     self.runner.events = Queue()
    #     for _n in range(2):
    #         event = Mock(key='event_{}'.format(_n))
    #         self.runner.events.put(event)

    #     response = requests.get(self.url + '/events')
    #     assert response.status_code == 200

    #     expected = [{'key': 'event_0'}, {'key': 'event_1'}]
    #     assert response.json() == expected
