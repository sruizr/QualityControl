import requests
from queue import Queue
from unittest.mock import Mock
from quactrl.rest.testing import AuTestResource
from tests.rest import TestResource


class An_AuTestResource(TestResource):
    def setup_class(cls):
        # Patch runner
        cls.create_patches([
            'quactrl.rest.testing.AuTestResource.runner',
            'quactrl.rest.testing.parsing'
        ])
        TestResource.setup_class(AuTestResource)

    def setup_method(self, method):
        self.resource = AutoTest
        self.parse.from_obj = lambda obj: {'key': obj.key}

    def should_return_open_tests(self):
        self.runner.tests = [Mock(key='test_{}'.format(_n))
                             for _n in range(2)]

        # Get all tests
        response = requests.get(self.url)

        assert response.status_code == 200
        expected = [
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
        self.runner.stop.return_value = {'info': 1}
        response = requests.delete(self.url + '/1')
        assert response.status_code == 200
        self.runner.stop.assert_called_with(0)

        assert response.json() == {'info': 1}

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
