import pytest
import cherrypy
import requests
from queue import Queue
from unittest.mock import patch, Mock
from quactrl.services.testing import AuTestResource, Parser
# from quactrl.helpers.rest import RestTester  #


class A_Patcher:

    def setup_method(self, method):
        self.parser = Parser()
        self.parser.parse_mock = lambda m: {'key': m.key}

    def should_select_suitable_method_from_class_name(self):
        mock = Mock()
        self.parser.parse_mock = Mock()

        self.parser.parse(mock)

        self.parser.parse_mock.assert_called_with(mock)

    def should_parse_part(self):
        part = Mock()
        part.tracking = '123456789'
        part.resource.name = 'part_name'
        part.resource.key = 'part_number'
        part.resource.description = 'part description'
        result = self.parser.parse_part(part)
        expected = {
            'type': 'Part',
            'tracking': '123456789',
            'name': 'part_name',
            'key': 'part_number',
            'description': 'part description'
        }
        assert result == expected

    def should_parse_test(self):
        self.parser.parse_part = lambda x: {'key': 'part'}

        test = Mock()
        part = Mock()
        part.__class__.__name__ = 'Part'
        test.path.description = 'Control plan description'
        test.path.id = 1234
        test.status = 'iddle'
        test.responsible.key = 'sruiz'

        result = self.parser.parse_test(test)

        expected = {
            'status': 'iddle',
            'type': 'Test',
            'test_description': 'Control plan description',
            'part': {'key': 'part'},
            'responsible_key': 'sruiz'
        }
        assert result == expected

        result = self.parser.parse_test(None)
        assert result == {'status': 'waiting',
                          'type': 'Test'}

    def should_parse_event(self):
        self.parser.parse_mock = lambda m: {'key': m.key}
        obj = Mock(key='obj')
        event = Mock()
        event.signal = 'signal'
        event.obj = obj
        del event.pars

        event_data = self.parser.parse_event(event)
        expected = {
            'signal': 'signal',
            'obj': {'key': 'obj'},
        }

        assert event_data == expected

        event.pars = {'foo': 'foo'}
        event_data = self.parser.parse_event(event)
        expected['pars'] = {'foo': 'foo'}

        assert event_data == expected

    def should_parse_check(self):
        check = Mock()
        check.path.description = 'check description'
        check.measures = [Mock(key='measure_{}'.format(_i))
                          for _i in range(1)]
        check.defects = [Mock(key='defect_{}'.format(_i))
                              for _i in range(2)]
        check.result = 'nok'

        check_data = self.parser.parse_check(check, '1.1')

        expected = {
            'type': 'Check',
            'id': '1.1',
            'description': 'Check description',
            'defects': [{'key': 'defect_0'}, {'key': 'defect_1'}],
            'measures': [{'key': 'measure_0'}],
            'result': 'nok'
        }
        assert check_data == expected

    def should_parse_measure(self):
        measure = Mock()
        measure.characteristic.key = 'char'
        measure.qty = 1.2
        measure_data = self.parser.parse_measure(measure)

        expected = {
            'type': 'Measure',
            'characteristic': {'key': 'char'},
            'value': 1.2
        }
        assert measure_data == expected

    def should_parse_characteristic(self):
        characteristic = Mock()
        characteristic.description = 'char description'
        characteristic.key = 'char_key'
        char_data = self.parser.parse_characteristic(characteristic)

        expected = {'type': 'Characteristic',
                    'description': 'Char description',
                    'key': 'char_key'
        }
        assert char_data == expected

    def should_parse_defect(self):
        defect = Mock()
        defect.description = 'defect description'
        defect.characteristic.key = 'char'

        defect_data = self.parser.parse_defect(defect)
        expected = {
            'type': 'Defect',
            'description': 'Defect description',
            'char_key': 'char'
        }

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
        cherrypy.engine.start()

    def teardown_class(cls):
        cls._runner_patcher.stop()
        cls._parser_patcher.stop()
        cherrypy.engine.exit()

    def setup_method(self, method):
        self.parser.parse = lambda obj: {'key': obj.key}

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
            'part_number': 'part_number',
            'responsible_key': 'sruiz',
            'cavity': 1
        }

        response = requests.post(self.url,
                                 json=json_req)

        assert response.status_code == 200
        expected = {'key': 'test_0'}
        assert response.json() == expected

        json_req['cavity'] = 2

        response = requests.post(self.url, json=json_req)
        assert response.json() == {'key': 'test_1'}
        self.runner.start_test.assert_called_with(
            {'tracking': '123456789',
             'part_name': 'part_name',
             'part_number': 'part_number'},
            'sruiz',
            cavity=2)

    def should_stop_any_test(self):
        response = requests.delete(self.url + '/1')
        assert response.status_code == 200
        self.runner.stop.assert_called_with(0)

        response = requests.delete(self.url)
        assert response.status_code == 200
        self.runner.stop.assert_called_with()

    def should_report_events(self):
        self.runner.events = Queue()
        for _n in range(2):
            event = Mock(key='event_{}'.format(_n))
            self.runner.events.put(event)

        response = requests.get(self.url + '/events')
        assert response.status_code == 200

        expected = [{'key': 'event_0'}, {'key': 'event_1'}]

        assert response.json() == expected
