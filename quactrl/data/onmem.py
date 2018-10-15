from quactrl.models.operations import PartModel, Part_Group


class Session:
    _Routes = {}
    _Parts = {}
    _Persons = {}
    _Locations = {}
    _PartModels = {}
    _Tests = []

    def commit(self):
        pass


class Repository:
    def __init__(self, session):
        self.session = session


class LocationRepo(Repository):
    def get_by_key(self, key):
        return self.session._Locations[key]

    def add(self, location):
        self.session._Locations[location.key] = location


class PersonRepo(Repository):
    def get_by_key(self, key):
        return self.session._Persons[key]

    def add(self, person):
        self.session._Persons[person.key] = person


class PartModelsRepo(Repository):

    def add(self, part_model):
        self.session._PartModels[part_model.part_number] = part_model

    def get_by_part_number(self, key):
        return self.session._PartModels[key]


class RouteRepo(Repository):
    def add(self, route):
        location = route.from_node
        resources = []
        for resource_map in route.outputs:
            resource = resource_map.resource
            resources.append(resource)
        for resource in resources:
            self.session._Routes[(resource, location)]

    def get_by_part_model_and_location(self, part_model, location):
        key = (part_model, location)
        if key in self.session._Routes:
            return self.session._Routes[key]

        for group in part_model.groups:
            key = (group, location)
            if key in self.sessionn._Routes:
                return self.session._Routes[key]

class BatchRepo(Repository):
    pass

class PartRepo(Repository):
    def get_or_create(self, location, )


class Test(Repository):
    def add(self, test):
        self.session._Tests.append(test)
