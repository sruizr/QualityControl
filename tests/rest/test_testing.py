import pytest
import requests
from queue import Queue
from unittest.mock import Mock
from quactrl.rest.testing import AuTestResource
from quactrl.managers.testing import TestManager
from tests.rest import TestResource


class An_AuTestResource(TestResource):
    def setup_class(cls):
        TestResource.setup_class(AuTestResource)

    def setup_method(self, method):
        # Patch manager
        self.create_patches([
            'quactrl.rest.testing.TestManager',
            'quactrl.rest.testing.parsing'
        ])
        self.manager = self.resource.manager = self.TestManager.return_value

        self.manager.testers = [Mock() for _ in range(3)]  # 3 cavities
        self.parsing.parse.return_value = lambda obj: {'key': obj.key}

    @pytest.mark.current
    def should_setup_from_PUT_request(self):
        data = {'par': 'value'}
        url = self.url + '/database'
        response = requests.put(url, json=data)

        assert response.status_code == 200
        self.manager.connect.assert_called_with(**data)

        url = self.url + '/setup'
        data = {'location_key': 'loc', 'process_key': 'keyp'}
        response = requests.put(url, json=data)
        assert response.status_code == 200
        self.manager.setup.assert_called_with(**data)

        response = requests.put(self.url + '/invalid', json=data)
        assert response.status_code == 404

        self.manager.connect.side_effect = [Exception()]
        response = requests.put(self.url + '/database', json=data)
        assert response.status_code == 500

    @pytest.mark.current
    def should_begin_test_from_order_on_cavity_1(self):
        order = ({
            'tracking': '123456789',
            'part_name': 'part_name',
            'part_number': 'part_number'},
            'sruiz'
        )

        response = requests.post(self.url + '/1',
                                json=order)

        assert response.status_code == 200
        self.resource.manager.start_test.assert_called_with(
            *order, 1
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

    def should_list_all_events_of_all_cavities(self):
        self.resource.handle_get_events = Mock()
        self.manager.cavities = 3
        self.resource.handle_get_events.return_value = 'response'

        response = requests.get(self.url + '/events')

        assert response.status_code == 200
        assert response.json() == 'response'
        self.resource.handle_get_events.assert_called_with(None, False)


        self.manager.cavities = 1
        response = requests.get(self.url + '/events')

        assert response.status_code == 200
        self.resource.handle_get_events.assert_called_with(1, False)

    def should_list_all_events_of_a_cavity(self):
        self.resource.handle_get_events = Mock()
        self.manager.cavities = 3
        self.resource.handle_get_events.return_value = 'response'

        response = requests.get(self.url + '/events/2')

        assert response.status_code == 200
        assert response.json() == 'response'
        self.resource.handle_get_events.assert_called_with(2, False)


    def should_list_last_events(self):
        self.resource.handle_get_events = Mock()
        self.resource.handle_get_events.return_value = 'response'
        self.manager.cavities = 3

        response = requests.get(self.url + '/events?last')

        assert response.status_code == 200
        self.resource.handle_get_events.assert_called_with(None, True)

    def should_report_test_status(self):
        self.resource.handle_get_tests = Mock()
        self.resource.handle_get_tests.return_value = 'response'
        self.manager.cavities = 3

        response = requests.get(self.url)

        assert response.status_code == 200
        assert response.json() == 'response'
        self.resource.handle_get_tests.assert_called_with(None)

        self.manager.cavities = 1
        response = requests.get(self.url)
        self.resource.handle_get_tests.assert_called_with(1)

        self.manager.cavities = 3
        response = requests.get(self.url + '/2')
        self.resource.handle_get_tests.assert_called_with(2)

    def should_handle_get_events(self):
        self.manager.events = [_ for _ in range(3)]
        self.manager.download_events.return_value = 'events'
        import pdb; pdb.set_trace()

        events = self.resource.handle_get_events(1, True)
        self.manager.download_events.assert_called_with(1)
        self.parsing.parse.assert_called_with('events', 4)
        assert events == self.parsing.parse.return_value

        events = self.resource.handle_get_events(2, False)
        self.parsing.parse.assert_called_with(1, 4)
        assert events == self.parsing.parse.return_value

        events = self.resource.handle_get_events(None, False)
        self.parsing.parse.assert_called_with([0, 1, 2], 4)
        assert events == self.parsing.parse.return_value

    def should_handle_get_tests(self):
        self.manager.cavities = 3

        response = self.resource.handle_get_tests(None)

        tests = [tester.test for tester in self.manager.testers]
        self.parsing.parse.assert_called_with(tests, 3)
        assert response == self.parsing.parse.return_value

        response = self.resource.handle_get_tests(2)
        self.parsing.parse.assert_called_with(self.manager.testers[1].test, 3)

        self.manager.cavities = 1
        response = self.resource.handle_get_tests(None)
        self.parsing.parse.assert_called_with(self.manager.testers[0].test, 3)
