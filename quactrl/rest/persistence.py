import cherrypy
import json
from quactrl.domain.persistence import dal
from quactrl.rest.parsers import ParserToDict, ParserToDomain


@cherrypy.expose
class DomainResource:

    def __init__(self, **parsers):
        self._parsers = parsers

    def _cp_dispatch(self, vpath):
        pass

    @cherrypy.tools.json_out()
    def GET(self):
        """Return the data of object by key"""
        pass

    @cherrypy.tools.json_in()
    def POST(self):
        """Creates entities on domain"""
        req = cherrypy.request
        data = req.json

        if req.params.get('entity') == 'bulk':
            try:
                _bulk_load(json.loads(req.json))
            except Exception as e:
                cherrypy.response.status = 101
                cherrypy.response.body = str(e)
        else:
           pass

    def DELETE(self):
        """Clears all database"""
        dal.clear_all_data()


class BulkProcessor:
    def __init__(self):
        pass

    def load(self, data):
        # Loading persons

        nodes = {}
        for record in data.get(persons, []):
            persons[record[key]] = plan.Person(**record)

        # Loading groups
        for record in data.get(groups, []):
            group = plan.Group(record['key'])
            for key in record['persons']:
                group.add_person(persons[key])
            groups[record['key']] = group

        # Locations
        for record in data.get(locations, []):
            locations[record['key']] = plan.Location(**record)

        # Resources
        resources = {}

        # Part Models


        # Device Models






        # Characteristics


        # Devices


        # Paths
        paths = {}
        for record in data.get('paths', []):
            path = self._create_path(record, nodes, resources)

        session = dal.Session()
        session.add_all(
            [nodes, resources, items, paths]
        )
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
