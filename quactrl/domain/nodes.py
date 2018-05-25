from sqlalchemy.orm import relationship
from quactrl.domain.base import (
    Node, NodeLink
)


class Person(Node):
    __mapper_args__ = {'polymorphic_identity': 'person'}
    roles = relationship('Roles',
                         foreign_keys=[NodeLink.to_node_id])
    reports_to = None
    in_charge_of = None

    def __init__(self, key, **kwargs):
        self.key = key
        self.name = kwargs.get('name', '')
        self.description = kwargs.get('description')


class Roles(Node):
    __mapper_args__ = {'polymorphic_identity': 'roles'}
    members = relationship('Person',
                           foreign_keys=[NodeLink.from_node_id])


class Location(Node):
    """Phisycal location for parts"""
    __mapper_args__ = {'polymorphic_identity': 'location'}
    site = relationship('Location')
    boxes = relationship('Location', foreign_key=[])
    owners = None


class InBox(Node):
    """Node for storing process instances"""
    __mapper_args__ = {'polymorphic_identity': 'inbox'}
    owners = None


class Library(Node):
    __mapper_args__ = {'polymorphic_identity': 'library'}
