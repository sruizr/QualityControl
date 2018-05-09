import pytest
import cherrypy
import requests
from quactrl.rest.devices import DeviceResource
from unittest.mock import patch, Mock
from tests.rest import TestResource
# from quactrl.helpers.rest import RestTester  #


class A_DeviceResource(TestResource):
    def setup_class(cls):
        # Patch runner
        cls.create_patches([
            'quactrl.rest.devices.DeviceManager',
            'quactrl.rest.devices.dal',
            'quactrl.rest.devices.DeviceProxy'
        ])
        TestResource.setup_class(DeviceResource)

    def should_return_devices_status(self):
        device_manager = self.DeviceManager.return_value
        device_manager.devices = {
            'single': Mock(),
            'multiple': {
                '001': Mock(),
                '002': Mock()
            }
        }
        device = device_manager.devices['single']

        device.is_bussy.return_value = True
        url = self.url + '/single'
        response = requests.get(url)
        assert response.status_code == 200
        assert response.json() == {'status': 'iddle'}

        device.is_bussy.return_value = False
        response = requests.get(url)
        assert response.json() == {'status': 'waiting'}


        for device in device_manager.devices['multiple'].values():
            device.is_bussy.return_value = False
        url = self.url + '/multiple'
        response = requests.get(url)
        expected = {'001': {'status': 'waiting'},
                    '002': {'status': 'waiting'}
        }
        assert response.json() == expected


        url = self.url + '/absent'
        response = requests.get(url)
        assert response.status_code == 404

    def should_load_devices_to_repository_from_device_info(self):
        device_manager = self.DeviceManager.return_value
        device = self.DeviceProxy.return_value

        device_info = {
            'name': 'name1',
            'class_name': 'fake.Device',
            'tracking': 'track',
            'par': 1
        }

        response = requests.put(self.url, json=device_info)
        assert response.status_code == 200

        self.DeviceProxy.assert_called_with('name1', 'track', device_info)
        device_manager.__setitem__.assert_called_with('name1', device)

    def should_load_devices_from_database(self):
        device_manager = self.DeviceManager.return_value
        device = self.DeviceProxy.return_value

        self.dal.is_connected.return_value = True
        response = requests.put(self.url + '/loc', json={})
        assert response.status_code == 200
        device_manager.load_devs_from.assert_called_with('loc')

    def should_avoid_load_devices_from_database_if_not_connected(self):
        device_manager = self.DeviceManager.return_value
        device = self.DeviceProxy.return_value

        self.dal.is_connected.return_value = False
        response = requests.put(self.url + '/loc', json={})
        assert response.status_code == 500
        device_manager.load_devs_from.assert_called_with('loc')

    def should_load_database(self):
        pass


    # def _should_setup_from_PUT_request(self):
    #     self.runner.set_location.side_effect = [None, Exception()]

    #     url = self.url + '/fake'
    #     response = requests.put(url)

    #     assert response.status_code == 200
    #     expected = {'status': 'done',
    #                 'location': 'fake'}
    #     assert response.json() == expected

    #     response = requests.put(self.url + '/invalid')
    #     assert response.status_code == 500

    # def _should_begin_test_from_part_information(self):
    #     json_req = {
    #         'tracking': '123456789',
    #         'part_name': 'part_name',
    #         'part_number': 'part_number',
    #         'responsible_key': 'sruiz',
    #         'cavity': 1
    #     }

    #     response = requests.post(self.url,
    #                              json=json_req)

    #     assert response.status_code == 200
    #     expected = {'key': 'test_0'}
    #     assert response.json() == expected

    #     json_req['cavity'] = 2

    #     response = requests.post(self.url, json=json_req)
    #     assert response.json() == {'key': 'test_1'}
    #     self.runner.start_test.assert_called_with(
    #         {'tracking': '123456789',
    #          'part_name': 'part_name',
    #          'part_number': 'part_number'},
    #         'sruiz',
    #         cavity=2)

    def should_stop_any_test(self):
        device_manager = self.DeviceManager.return_value

        device_manager.devices = {'name{}'.format(i): Mock()
                                  for i in range(3)}

        response = requests.delete(self.url + '/name0')
        assert response.status_code == 200
        assert len(device_manager.devices) == 2

        response = requests.delete(self.url + '/unknow')
        assert response.status_code == 404

        response = requests.delete(self.url)
        assert response.status_code == 200
        assert len(device_manager.devices) == 0
