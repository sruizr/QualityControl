class Session:
    _Routes = {}
    _Parts = {}
    _Persons = {}
    _Locations = {}
    _PartModels = {}

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
    def get_by_part_number(self, key):
        return self.session._PartModels[key]


class RouteRepo(Repository):
    def get_by_part_model_and_location(self, part_model, location):
