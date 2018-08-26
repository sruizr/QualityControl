import requests
from unittest.mock import Mock
from quactrl.rest.crud import CrudResource
from tests.rest import TestResource
import pytest


class A_CrudResource(TestResource):
    def setup_class(cls):
        TestResource.setup_class(CrudResource)

    def setup_method(self, method):
        self.create_patches([
            'quactrl.rest.crud.Crud',
            'quactrl.rest.crud.parsing'
        ])
        self.resource.manager = self.manager = self.Crud.return_value

    @pytest.mark.current
    def should_query_a_unique_domain_object(self):
        url = self.url + '/fakeclass?resource_name=name'
        expected = {
            'class_name': 'fakeClass',
            'id': 10
        }
        self.parsing.parse.return_value = expected
        self.manager.read.return_value = [Mock(name='fake_object')]
        response = requests.get(url)

        self.manager.read.assert_called_with('fakeclass', resource_name='name')
        assert response.json() == expected

    @pytest.mark.current
    def should_query_many_domain_object(self):

        url = self.url + '/fakeclass?resource_name=name'
        expected = {
            'class_name': 'fakeClass',
            'id': 10

        }
        self.parsing.parse.return_value = expected
        self.manager.read.return_value = [Mock() for _ in range(2)]

        response = requests.get(url)

        self.manager.read.assert_called_with('fakeclass', resource_name='name')
        assert response.json() == [expected, expected]
        assert response.status_code == 200

    def should_config_data_connection(self):
        json_data = {'connection_string': 'connstr'}

        self.manager.connect.return_value = True

        # Successfull data connection
        response = requests.put(self.url, json=json_data)
        assert response.status_code == 202
        self.manager.connect.assert_called_with(json_data)

        # Unsuccessfull data connection
        self.manager.connect.return_value = False
        response = requests.put(self.url, json=json_data)
        assert response.status_code == 404

    def should_create_domain_object_successfully(self):
        fields = {'key': 'key'}
        expected = {'id': 1, 'class_name': 'fake', 'key': 'key'}

        new_obj = Mock()
        self.manager.create.return_value = new_obj
        self.parsing.parse.return_value = expected
        url = self.url + '/class_name'
        response = requests.post(url, json=fields)

        self.manager.create.assert_called_with('class_name', **fields)
        self.parsing.parse.assert_called_with(new_obj)
        assert response.status_code == 201
        assert response.json() == expected

    def should_not_create_domain_object_if_duplicated(self):
        fields = {'key': 'key'}
        expected = {'id': 1, 'class_name': 'fake', 'key': 'key'}

        self.manager.create.return_value = None
        self.parsing.parse.return_value = expected
        parse_calls = len(self.parsing.parse.mock_calls)

        url = self.url + '/class_name'
        response = requests.post(url, json=fields)

        assert parse_calls == len(self.parsing.parse.mock_calls)
        assert response.status_code == 409
        assert not response.json()

    def should_update_domain_objects(self):
        fields = {'par1': 'fake', 'par2': 1, 'key': 'key'}
        expected = {'id': 1, 'class_name': 'fake', 'key': 'other key'}

        updated_obj = Mock()
        self.manager.update.return_value = updated_obj
        self.parsing.parse.return_value = expected

        url = self.url + '/fake/2'
        response = requests.patch(url, json=fields)

        self.manager.update.assert_called_with('fake', 2, key='key', par1='fake', par2=1)
        self.parsing.parse.assert_called_with(updated_obj)
        assert response.status_code == 201
        assert response.json() == expected

    def should_remove_domain_objectes(self):
        url = self.url + '/person/1'
        response = requests.delete(url)

        self.manager.delete.assert_called_with('person', 1)
        assert response.status_code == 200
