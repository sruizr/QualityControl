import pytest

current = pytest.mark.current


class TestWithPatches:
    pass


class DataTest:
    def setup_method(self, method):
        self.session = dal.Session()

    def teardown_method(self, method):
        self.session.rollback()
        self.session.close()
