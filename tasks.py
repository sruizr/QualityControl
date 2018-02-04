import os
from invoke import task
from unittest.mock import Mock
from quactrl.app.app import Environment
from quactrl.domain.data import DataAccessLayer
from tests.integration.loaders import Filler


@task
def loaddb(cntx, filename):
    dal = DataAccessLayer()
    full_fn = os.path.join(os.getcwd(), filename)
    conn_string = 'sqlite:///' + full_fn

    dal.db_init(conn_string)
    dal.prepare_db()
    dal.clear_all_data()
    filler = Filler(dal)
    dal.load_db(filler)
