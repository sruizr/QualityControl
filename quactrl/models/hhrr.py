from .core import Node


class Person(Node):
    """Person with repsonability capbilities
    """
    def __init__(self, key, name, full_name):
        self.key = key
        self.name = name
        self.description = full_name

        self.roles = []

    def add_role(self, role):
        if role not in self.roles:
            self.roles.append(role)
            role.add_person(self)


class Role(Node):
    """Role linked to persons
    """
    def __init__(self, key, name, description=None):
        self.key = key
        self.name = name
        self.description = description

        self.persons = []


    def add_person(self, person):
        if person not in self.persons:
            self.persons.append(person)
            person.add_role(self)
