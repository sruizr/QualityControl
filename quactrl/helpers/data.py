import requests


class Loader:
    def __init__(self, url):
        self.url = url
        response = requests.get(self.url)

    def connect_database(self, **kwargs):
        """Loads database from connection parameters"""
        response = requests.put(self.url, json=kwargs)
        assert response.status_code == 200

    def load(self, name, data):
        obj_list = data[name + 's']
        path = '/' + name
        obj_name = name.capitalize()
        self._load(path, obj_list, obj_name)

    def _load(self, path, obj_list, name):
        url = self.url + path
        for obj in obj_list:
            response = requests.post(url, json=obj)
            if response.status_code == 409:
                print('{}: {} already exists, not created'.format(name, obj))
                if response.status_code not in (409, 202):
                    print('UNKNOWN ERROR')
                    print(response.content)
