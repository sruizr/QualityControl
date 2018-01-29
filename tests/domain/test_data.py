from quactrl.domain.data import DataAccessLayer


class A_DataAccessLayer:
    pass


class OnMemoryTest:
    dal = DataAccessLayer()
    dal.db_init('sqlite:///:memory:', False)
    dal.prepare_db()

    def setup_method(self, method):
        self._transaction = self.dal.connection.begin()
        self.session = self.dal.Session(bind=self.dal.connection)

    def teardown_method(self, method):
        # self.session.rollback()
        self._transaction.rollback()
        self.session.close()

def load_data(dal):
    session = dal.Session()



    session.add_all([])
    session.commit()
