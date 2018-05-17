from quactrl.domain.base import Node, NodeRelation


class Person(Node):
    __mapper_args__ = {'polymorphic_identity': 'person'}

    def __init__(self, key, **kwargs):
        self.key = key
        self.name = kwargs.get('name', '')
        self.description = kwargs.get('description')


class Group(Node):
    __mapper_args__ = {'polymorphic_identity': 'group'}

    def add_person(self, *persons):
        for person in persons:
            NodeRelation(self, person)

    def get_persons(self):
        persons = []
        for destination in self.destinations:
            if (destination.relation_class == 'contains' and
                    type(destination.to_node) is Person):
                persons.append(self.destinations.to_node)
        return persons


class Location(Node):
    __mapper_args__ = {'polymorphic_identity': 'location'}

    def __init__(self, key, name=''):
        self.key = key
        self.name = name

    def add_devices(self, *devices):
        for device in devices:
            if device.is_a == 'device':
                pass
