from invoke import task
from urllib.parse import parse
from quactrl.rest import App
from quactrl.helpers import get_class


@task
def start(cntx, resources, url):
    full_name = 'quactrl.rest.' + class_name
    Resource = get_class(full_name)

    app = App()
    app.add_resource(Resource(), name)
    app.run()
