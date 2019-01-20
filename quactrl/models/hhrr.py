from .core import Node


class Person(Node):
    """Person with repsonability capbilities
    """
    def __init__(self, key, name, full_name):
        self.key = key
        self.name = name
        self.description = full_name

        self.roles = []


class Role(Node):
    """Role linked to persons
    """
    def __init__(self, key, name, description=None):
        self.key = key
        self.name = name
        self.description = description

        self.persons = []
