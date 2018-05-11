import os
from unittest.mock import Mock
from quactrl.domain.persistence import DataAccessLayer
from quactrl.services.common import OneItemFlowService
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

    # def setup_method(self, method):
    #     self._transaction = self.dal.connection.begin()
    #     self.session = self.dal.Session(bind=self.dal.connection)

    # def teardown_method(self, method):
    #     # self.session.rollback()
    #     self._transaction.rollback()
    #     self.session.close()


class A_Service(OnFileTest):

    def setup_method(self, method):

        self.env = Mock()
        self.env.dal = self.dal

        self.env.location_key = 'wip'
        self.env.operation_name = 'Test'


    def should_init_service(self):

        service = OneItemFlowService(self.env)

        assert service.operation.adapter

        service.start()
        service.stop()

        while service.generator.is_alive():
            pass

        while service.operation.is_alive():
            pass


    def should_run_process_one_part_from_generator(self):
        service = OneItemFlowService(self.env)

        service.start()
        service.enter_item({'resource_key': 'partnumber', 'tracking': 'part_track'}, '007')
        service.stop()

        while service.generator.is_alive():
            pass

        while service.operation.is_alive():
            pass
