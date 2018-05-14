import requests
from unittest.mock import patch, Mock
from quactrl.rest.domain import DomainResource
from tests.rest import TestResource


class An_AuTestResource(TestResource):
    def setup_class(cls):
        cls.create_patches([
            'quactrl.rest.domain.dal',
            'quactrl.rest.domain.parse'
        ])
        TestResource.setup_class(DomainResource)

    def should_query_a_unique_domain_object(self):
        url = self.url + '/fakeclass?resource_name=name'
        expected = {
            'class_name': 'fakeClass',
            'id': 10

        }
        self.parse.from_obj.return_value = expected
        self.dal.get.return_value = [Mock(name='fake_object')]
        response = requests.get(url)

        self.dal.get.assert_called_with('fakeclass', resource_name='name')
        assert response.json() == expected


    def should_query_many_domain_object(self):

        url = self.url + '/fakeclass?resource_name=name'
        expected = {
            'class_name': 'fakeClass',
            'id': 10

        }
        self.parse.from_obj.return_value = expected
        self.dal.get.return_value = [Mock() for _ in range(2)]

        response = requests.get(url)

        self.dal.get.assert_called_with('fakeclass', resource_name='name')
        assert response.json() == [expected, expected]
        assert response.status_code == 200

    def should_config_data_connection(self):
        json_data = {'connection_string': 'connstr'}

        self.dal.connect.return_value = True

        # Successfull data connection
        response = requests.put(self.url, json=json_data)
        assert response.status_code == 202
        self.dal.connect.assert_called_with('connstr')

        # Unsuccessfull data connection
        self.dal.connect.return_value = False
        response = requests.put(self.url, json=json_data)
        assert response.status_code == 404

    def should_create_domain_object_successfully(self):
        obj_data = {'class_name': 'fake', 'key': 'key'}
        expected = {'id': 1, 'class_name': 'fake', 'key': 'key'}

        new_obj = Mock()
        self.dal.create.return_value = new_obj
        self.parse.from_obj.return_value = expected

        response = requests.post(self.url, json=obj_data)

        self.parse.from_obj.assert_called_with(new_obj)
        assert response.status_code == 201
        assert response.json() == expected

    def should_not_create_domain_object_if_duplicated(self):
        obj_data = {'class_name': 'fake', 'key': 'key'}
        expected = {'id': 1, 'class_name': 'fake', 'key': 'key'}

        new_obj = Mock()
        self.dal.create.return_value = None
        self.parse.from_obj.return_value = expected
        parse_calls = len(self.parse.from_obj.mock_calls)

        response = requests.post(self.url, json=obj_data)

        assert parse_calls == len(self.parse.from_obj.mock_calls)
        assert response.status_code == 409
        assert not response.json()


    def should_update_domain_objects(self):
        obj_data = {'class_name': 'fake', 'id': 1, 'key': 'key'}
        expected = {'id': 1, 'class_name': 'fake', 'key': 'other key'}

        updated_obj = Mock()
        self.dal.update.return_value = updated_obj
        self.parse.from_obj.return_value = expected

        response = requests.patch(self.url, json=obj_data)

        self.dal.update.assert_called_with('fake', id=1, key='key')
        self.parse.from_obj.assert_called_with(updated_obj)
        assert response.status_code == 201
        assert response.json() == expected

    def should_remove_domain_objectes(self):
        del_data = {'class_name': 'person', 'id': 1}

        response = requests.delete(self.url, json=del_data)

        self.dal.remove.assert_called_with('person', 1)
        assert response.status_code == 200
