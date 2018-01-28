from datetime import datetime
from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import (
    String, Integer, DateTime, Float
    )
from sqlalchemy.orm import relationship
from quactrl.domain.data import DataAccessLayer as Dal
import pdb


class Resource(Dal.Base):
    __tablename__ = 'resource'
    is_a = Column(String)
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    name = Column(String)
    description = Column(String)


class ResourceRelation(Dal.Base):
    __tablename__ = 'resource_relation'

    id = Column(Integer, primary_key=True)
    relation_class = Column(String, default='contain')
    from_resource_id = Column(Integer, ForeignKey('resource.id'))
    to_resource_id = Column(Integer, ForeignKey('resource.id'))
    qty = Column(Float, default=1.0)

    from_resource = relationship('Resource', foreign_keys=[from_resource_id],
                                 backref='destinations')
    to_resource = relationship('Resource', foreign_keys=[to_resource_id])


class Node(Dal.Base):
    __tablename__ = 'node'
    is_a = Column(String)
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    name = Column(String)

    def __init__(self, key, description=None, name=None):
        self.key = key
        self.description = description
        self.name = name


class NodeRelation(Dal.Base):
    __tablename__ = 'node_relation'
    id = Column(Integer, primary_key=True)
    relation_class = Column(String, default='contains')
    qty = Column(Float, default=1.0)
    from_node_id = Column(Integer, ForeignKey('node.id'))
    to_node_id = Column(Integer, ForeignKey('node.id'))

    from_node = relationship('Node', foreign_keys=[from_node_id],
                             backref='destinations')
    to_node = relationship('Node', foreign_keys=[to_node_id])

    def __init__(self, from_node, to_node, relation='contains', qty=1.0):
        self.from_node = from_node
        self.to_node = to_node
        self.relation_class = relation
        self.qty = qty


class Item(Dal.Base):
    __tablename__ = 'item'
    is_a = Column(String)
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    resource_id = Column(ForeignKey('resource.id'))
    resource = relationship("Resource")
    tracking = Column(String, index=True)
    state = Column(String, index=True, default='active')

    def __init__(self, resource, tracking='', state='active'):
        self.resource = resource
        self.tracking = tracking
        self.state = state


class ItemRelation(Dal.Base):
    __tablename__ = 'item_relation'
    id = Column(Integer, primary_key=True)
    relation_class = Column(String, default='has')
    from_item_id = Column(Integer, ForeignKey('item.id'))
    to_item_id = Column(Integer, ForeignKey('item.id'))
    qty = Column(Float, default=1.0)

    from_item = relationship('Item', foreign_keys=[from_item_id])
    to_item = relationship('Item', foreign_keys=[to_item_id])


class Path(Dal.Base):
    __tablename__ = 'path'
    is_a = Column(String(15))
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('path.id'))
    sequence = Column(Integer, default=0)
    key = Column(String)
    description = Column(String)
    from_node_id = Column(Integer, ForeignKey('node.id'), index=True)
    to_node_id = Column(Integer, ForeignKey('node.id'), index=True)

    from_node = relationship('Node', foreign_keys=[from_node_id])
    to_node = relationship('Node', foreign_keys=[to_node_id])

    resources = relationship('PathResource')


class PathResource(Dal.Base):
    __tablename__ = 'path_resource'

    id = Column(Integer, primary_key=True)
    resource_id = Column(Integer, ForeignKey('resource.id'))
    flow_class = Column(String(10), default='input')
    qty = Column(Float, default=1.0)
    path_id = Column(Integer, ForeignKey('path.id'), index=True)


class Movement(Dal.Base):
    __tablename__ = 'movement'
    id = Column(Integer, primary_key=True)
    item_id = Column(ForeignKey('item.id'), nullable=False)
    from_node_id = Column(Integer, ForeignKey('node.id'), index=True)
    to_node_id = Column(Integer, ForeignKey('node.id'), index=True)
    path_id = Column(Integer, ForeignKey('path.id'))
    input_on = Column(DateTime, default=datetime.now)
    output_on = Column(DateTime)
    qty = Column(Float, default=1.0)

    from_node = relationship('Node', foreign_keys=[from_node_id])
    to_node = relationship('Node', foreign_keys=[to_node_id])
    item = relationship('Item')
    path = relationship('Path')


class DataAccessModule:
    def __init__(self, dal):
        self.dal = dal

    def move_item(self, item, to_node=Node, path=None):
        pass
