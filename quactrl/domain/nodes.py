from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from quactrl.domain.base import (
    Node, NodeLink
)


class Role(Node):
    __mapper_args__ = {'polymorphic_identity': 'roles'}


class Person(Node):
    __mapper_args__ = {'polymorphic_identity': 'person'}
    roles = relationship('Role', secondary=NodeLink,
                         primaryjoin=Node.id==NodeLink.c.to_node_id,
                         secondaryjoin=Role.id==NodeLink.c.from_node_id,
                         backref='members')
    reports_to = None
    in_charge_of = None


class Location(Node):
    """Phisycal location for parts"""
    __mapper_args__ = {'polymorphic_identity': 'location'}

    parcels = relationship('Location', secondary=NodeLink,
                           primaryjoin=Node.id==NodeLink.c.from_node_id,
                           secondaryjoin=Node.id==NodeLink.c.to_node_id,
                           backref='_sites')

    owners = relationship('Role', secondary=NodeLink,
                          primaryjoin=Node.id==NodeLink.c.from_node_id,
                          secondaryjoin=Node.id==NodeLink.c.to_node_id)

    @hybrid_property
    def site(self):
        if len(self._sites) > 0:
            return self._sites[0]

    @site.setter
    def site(self, site):
        if len(self._sites) == 0:
            self._sites.append(site)
        else:
            self._sites[0] = site

class InBox(Node):
    """Node for storing process instances"""
    __mapper_args__ = {'polymorphic_identity': 'inbox'}


class Library(Node):
    __mapper_args__ = {'polymorphic_identity': 'library'}
