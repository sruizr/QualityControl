import os
from invoke import task
# from quactrl.app.app import Environment
# from quactrl.domain.persistence import DataAccessLayer
# from tests.integration.loaders import Filler
import quactrl.services.api as api
from quactrl.services import yaml


apps = {}


@task
def initdb(cntx, filename):
    dal = DataAccessLayer()
    full_fn = os.path.join(os.getcwd(), filename)
    conn_string = 'sqlite:///' + full_fn

    dal.db_init(conn_string)
    dal.prepare_db()
    dal.clear_all_data()
    filler = Filler(dal)
    dal.load_db(filler)


@task
def start(cntx, environment='production', config_fn=None):
    if environment in apps.keys():
        print("Environment {} is already started".format(environment))
        return

    if environment == 'fake':
        app = get_api_rest()
    else:
        if config_fn is None:
            print("It's needed a config file to start application")
            return
        with open(config_fn) as f:
            config = yaml.load(f)
            app = get_api_rest(config)

    apps[environment] = app
    app.run()

@task
def stop(cntx, environment='production'):
    if environment in apps.keys():
        apps.pop(environment)
        apps.stop()

    else:
        print('There is no {} started'.format(environment))


def start_fake_api_rest():
    config = {
        'host': 'fakehost',
        'port': 333,
        'services': ['tester'],
    }

    return api.run_fake(config)


def get_api_rest(config=None):

    return  api.App()
