from unittest.mock import patch
import pytest

current = pytest.mark.current


class TestWithPatches:
    def create_patches(self, definitions):
        self.patch = {}
        self._patchers = []
        for definition in definitions:
            patcher = patch(definition)
            name = definition.split('.')[-1]
            self.patch[name] = patcher.start()
            self._patchers.append(patcher)
            setattr(self, name, self.patch[name])

    def teardown_method(self, method):
        for patcher in self._patchers:
            patcher.stop()



class DataTest:
    def setup_method(self, method):
        self.session = dal.Session()

    def teardown_method(self, method):
        self.session.rollback()
        self.session.close()
