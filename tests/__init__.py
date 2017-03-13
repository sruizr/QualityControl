from quactrl import dal


class TestBase:

    @classmethod
    def setUpClass(cls):
        dal.db_init('sqlite:///:memory:', echo=True)
