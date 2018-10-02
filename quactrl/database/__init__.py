
class Repository:
    def __init__(self, session):
        self.session = session

    def add(self, entity):
        self.session.add(entity)

    def remove(self, entity):
        self.session.remove(entity)


class PartRepo(Repository):
    def get_or_create_part(self, location, responsible, **part_info):
        pass


class PartModelRepo(Repository):
    def get_by_part_number(self, part_number):
        pass


class RouteRepo(Repository):
    def get_by_part_model_and_location(self, part_model, location):
        pass


class PersonRepo(Repository):
    def get_by_key(self, key):
        pass
