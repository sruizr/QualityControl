import os
from quactrl.domain.data import DataAccessLayer
from tests.integration.loaders import Filler


filename = 'test_data.db'


def load_test_data(filename):
    full_fn = os.path.join(os.getcwd(), filename)
    if os.path.isfile(full_fn):
        os.remove(full_fn)

    conn_string = 'sqlite:///' + full_fn
    dal = DataAccessLayer()
    dal.db_init(conn_string)
    dal.prepare_db()
    dal.clear_all_data()
    filler = Filler(dal)
    dal.load_db(filler)


load_test_data(filename)


class OnFileTest:
    dal = DataAccessLayer()
    full_fn = os.path.join(os.getcwd(), filename)
    conn_string = 'sqlite:///' + full_fn
    dal.db_init(conn_string, False)
    dal.prepare_db()

    def setup_method(self, method):
        self._transaction = self.dal.connection.begin()
        self.session = self.dal.Session(bind=self.dal.connection)

    def teardown_method(self, method):
        # self.session.rollback()
        self._transaction.rollback()
        self.session.close()


# class A_Service(OnFileTest):

#     def should_load_operation(self):
#         operation = self.dal.plan.get_operation('final_test', '311574695')
#         print(self.dal.conn_string)
#         assert operation.children[0].children[0].method_name == 'en12830.eval_environment'

#     def should_load_operator(self):
#         person = self.dal.do.get_operator('438')
#         assert person.name == 'Salvador Ruiz'

#     def should_load_devices_by_location(self):
#         key = 'wip_eT'
#         location = self.dal.do.get_location(key)
#         devices = self.dal.do.get_devices_by_location(location)

#         assert devices['env_station'].behaviour.get_temperature()
#         assert devices['env_station'].behaviour.get_humidity()
#         assert devices['env_station'].behaviour.get_pressure()
