from quactrl import dal


class TestApp:

    @classmethod
    def setUpClass(cls):
        dal.db_init('sqlite:///:memory:')
