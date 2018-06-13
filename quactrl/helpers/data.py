import requests


class Loader:
    def __init__(self, url):
        self.url = url
        response = requests.get(self.url)

    def connect_database(self, **kwargs):
        """Loads database from connection parameters"""
        response = requests.put(self.url, json=kwargs)
        assert response.status_code == 200

    def load_persons(self, persons):
        self._load('/person', persons, 'Person')

    def load_locations(self, locations):
        self._load('/location', locations, 'Location')

    def load_part_models(self, part_models):
        self._load('/part_model', part_models, 'Part Model')

    def load_device_models(self, device_models):
        self._load('/device_model', device_models, 'Device Model')

    def load_devices(self, devices):
        self._load('/device', devices, 'Device')

    def load_paths(self, paths):
        self._load('/path', paths, 'Path')

    def _load(self, path, obj_list, name):
        url = self.url + path
        for obj in obj_list:
            response = requests.post(url, json=obj)
            if response.status_code == 409:
                print('{}: {} already exists, not created'.format(name, obj))
                if response.status_code not in (409, 202):
                    print('UNKNOWN ERROR')
                    print(response.content)
