from quactrl import dal
import pdb


class TestBase:

    @classmethod
    def setup_class(cls):
        dal.db_init('sqlite:///:memory:', echo=False)
        dal.prepare_db()

    def setup_method(self, method):
        dal.session = dal.Session()

    def teardown_method(self, method):
        dal.session.rollback()
        dal.session.close()
