import requests
from queue import Queue
from unittest.mock import Mock
from quactrl.rest.testing import AuTestResource
from tests.rest import TestResource


class An_AuTestResource(TestResource):
    def setup_class(cls):
        # Patch manager
        cls.create_patches([
            'quactrl.rest.testing.TestManager',
            'quactrl.rest.testing.parsing'
        ])
        TestResource.setup_class(AuTestResource)

    def setup_method(self, method):
        self.manager = self.resource.manager
        self.manager.testers = [Mock() for _ in range(3)]  # 3 cavities
        self.parsing.from_obj = lambda obj: {'key': obj.key}

    def _should_return_open_tests(self):
        self.manager.tests = [Mock(key='test_{}'.format(_n))
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

        data = {'par': 'value'}
        url = self.url + '/database'
        response = requests.put(url, json=data)

        assert response.status_code == 200
        self.manager.connect.assert_called_with(**data)

        url = self.url + '/setup'
        response = requests.put(url, json=data)
        assert response.status_code == 200
        self.manager.setup.assert_called_with(**data)

        response = requests.put(self.url + '/invalid', json=data)
        assert response.status_code == 404

        self.manager.connect.side_effect = [Exception()]
        response = requests.put(self.url + '/database', json=data)
        assert response.status_code == 500

    def should_begin_test_from_order_on_cavity_1(self):
        order = ({
            'tracking': '123456789',
            'part_name': 'part_name',
            'part_number': 'part_number'},
            'sruiz', {'par': 'value'}
        )

        response = requests.post(self.url,
                                 json=order)

        assert response.status_code == 200
        self.resource.manager.testers[0].start_test.assert_called_with(
            *order
        )

    def should_begin_test_from_order_on_cavity_3(self):
        order = ({
            'tracking': '123456789',
            'part_name': 'part_name',
            'part_number': 'part_number'},
            'sruiz', {'par': 'value'}
        )

        response = requests.post(self.url + '/3',
                                 json=order)

        assert response.status_code == 200
        self.resource.manager.testers[2].start_test.assert_called_with(
            *order
        )

    def should_stop_tests_on_multiple_cavities(self):
        self.manager.cavities = 3
        for index, tester in enumerate(self.manager.testers):
            tester.stop.return_value = [index]

        response = requests.delete(self.url + '/2')
        assert response.status_code == 200
        self.manager.testers[0].stop.assert_not_called()
        self.manager.testers[1].stop.assert_called_with()
        assert response.json() == [1]

        response = requests.delete(self.url)
        assert response.json() == [[0], [1], [2]]

    def should_stop_test_on_single_cavity_tool(self):
        self.manager.cavities = 1
        self.manager.testers[0].stop.return_value = 'foo'
        response = requests.delete(self.url)

        assert response.status_code == 200
        assert response.json() == 'foo'

    def _should_report_events(self):
        self.manager.events = Queue()
        for _n in range(2):
            event = Mock(key='event_{}'.format(_n))
            self.manager.events.put(event)

        response = requests.get(self.url + '/events')
        assert response.status_code == 200

        expected = [{'key': 'event_0'}, {'key': 'event_1'}]

        assert response.json() == expected

    def should_list_all_events_of_all_cavities(self):
        pass

    def should
