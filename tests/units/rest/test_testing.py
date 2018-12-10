import requests
import quactrl.rest.testing as t
from unittest.mock import Mock, call
from tests.units.rest import TestResource


class A_CavitiesResource(TestResource):
    def setup_class(cls):
        TestResource.setup_class(t.CavitiesResource)

    def setup_method(self, method):
        # Patch manager
        self.create_patches([
            'quactrl.rest.testing.parse'
        ])
        self.service = self.resource.service
        self.parse.return_value = lambda obj: {'key': obj.key}

    def should_start_cavity(self):
        requests.put(self.url + '/1')
        self.service.start_inspector.assert_called_with(1)
        response = requests.put(self.url + '/incorrect')
        assert response.status_code == 400

        requests.put(self.url)
        self.service.start_inspector.assert_called_with()

    def should_stop_cavity(self):
        requests.delete(self.url + '/1')
        self.service.stop_inspector.assert_called_with(1)
        requests.delete(self.url)
        self.service.stop_inspector.assert_called_with()
        assert requests.delete(self.url + '/incorect').status_code == 400


    def should_retrieve_cavity_status(self):
        self.parse.return_value = json_res = {'fake': 'json'}
        self.service.inspectors = {1: Mock(), 2: Mock()}
        self.service.active_cavities = [1, 2]

        response = requests.get(self.url + '/1')
        assert response.json() == json_res

        response = requests.get(self.url)
        assert response.json() == {'1': json_res, '2': json_res}

        assert call(self.service.inspectors[1]) in self.parse.mock_calls
        assert call(self.service.inspectors[2]) in self.parse.mock_calls

        assert requests.get(self.url + '/incorrect').status_code == 400


class A_PartModelResource:
    def should_retrieve_part_model(self):
        pass


class A_RootResource(TestResource):
    def setup_class(cls):
        TestResource.setup_class(t.RootResource, ['cavities'])

    def setup_method(self, method):
        # Patch manager
        self.create_patches([
            'quactrl.rest.testing.parse',
            'quactrl.rest.testing.os.system'
        ])
        self.service = self.resource.service
        self.parse.return_value = lambda obj: {'key': obj.key}

    def should_shutdown_computer(self):
        response = requests.delete(self.url)
        self.system.assert_called_with('shutdown now')
        assert response.status_code == 501

    def should_by_pass_cavities_resource(self):
        requests.put(self.url + '/cavities/1')
        self.service.start_inspector.assert_called_with(1)
