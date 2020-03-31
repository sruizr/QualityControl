from .core import Node


class Person(Node):
    """Person with responsability capbilities
    """
    def __init__(self, key, name, full_name, roles=None):
        self.key = key
        self.name = name
        self.description = full_name
        self.roles = []

        roles = [] if roles is None else roles
        for role in roles:
            self.add_role(role)

    def add_role(self, role):
        if role not in self.roles:
            self.roles.append(role)
            role.add_person(self)


class Role(Node):
    """Role linked to persons
    """
    def __init__(self, key, name, description=None, persons=None):
        self.key = key
        self.name = name
        self.description = description
        self.persons = []

        persons = [] if persons is None else persons
        for person in persons:
            self.add_person(person)

    def add_person(self, person):
        if person not in self.persons:
            self.persons.append(person)
            person.add_role(self)
