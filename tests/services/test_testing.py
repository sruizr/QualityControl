import pytest
import cherrypy
from unittest.mock import patch
from quactrl.services.testing  import AuTestResource
# from quactrl.helpers.rest import RestTester  #


class An_AuTestResource:
    def setup_class(cls):
         # Patch runner
        cls._patcher = patch('quactrl.services.testing.runner')
        cls.runner = cls._patcher.start()
        conf = {'/':{}}
        cherrypy.tree.mount(AuTestResource(), '/', conf)
        cls.url = 'http//localhost:8080/'
        cherrry.engine.start()

    def teardown_class(cls):
        cls._patcher.stop()
        cherrypy.engine.exit()

    def should_setup_from_PUT_request(self):
        url = self.url + '?location=fake'
        response = request.put(url)
        assert response.status_code == 200


    def should_redirect_part_info_request(self):

        answer = self.test_resource.GET(1)

    def should_start_test_from_part_info(self):
        part_info = {
            'resource_key': 'partnumber',
            'tracking': '123456789',
            'cavity': 1
        }
