from quactrl import dal


class TestBase:

    @classmethod
    def setup_class(cls):
        dal.db_init('sqlite:///:memory:', echo=True)
        dal.prepare_db()

    def setup_method(self, method):
        dal.session = dal.Session()

    def teardown_method(self, method):
        dal.session.rollback()
        dal.session.close()
