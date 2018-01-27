from datetime import datetime
import json
from sqlalchemy import create_engine, ForeignKey, Column, UniqueConstraint
from sqlalchemy.types import (
    String, Integer, DateTime, Float
    )
from sqlalchemy.orm import sessionmaker, backref, relationship
from quactrl.domain.data  import Base
import importlib
import pdb


class Resource(Base):
    __tablename__ = 'resource'
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    name = Column(String)
    description = Column(String)
    is_a = Column(String)
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

class ResourceRelation(Base):
    __tablename__ = 'resource_relation'
    id = Column(Integer, primary_key=True)
    relation_class = Column(String, default='has')
    from_resource_id = Column(Integer, ForeignKey('resource.id'))
    to_resource_id = Column(Integer, ForeignKey('resource.id'))
    qty = Column(Float, default=1.0)

    from_resource = relationship('Resource', foreign_keys=['from_resource_id'])
    to_resource = relationship('Resource', foreign_keys=['to_resource_id'])


class Node(Base):
    __tablename__ = 'node'
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    name = Column(String)
    is_a = Column(String)
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

class NodeRelation(Base):
    __tablename__ = 'node_relation'
    id = Column(Integer, primary_key=True)
    relation_class = Column(String, default='has')
    from_node_id = Column(Integer, ForeignKey('node.id'))
    to_node_id = Column(Integer, ForeignKey('node.id'))
    qty = Column(Float, default=1.0)

    from_node = relationship('Node', foreign_keys=['from_node_id'])
    to_node = relationship('Node', foreign_keys=['to_node_id'])

class Item(Base):
    __tablename__ = 'item'
    resource_id = Column(ForeignKey('resource.id'))
    resource = relationship("Resource")
    tracking = Column(String, index=True)
    state = Column(String, index=True, default='active')
    is_a = Column(String)

    __mapper_args__ = {
        'polymorphic_on': is_a
    }

class ItemRelation(Base):
    __tablename__ = 'item_relation'
    id = Column(Integer, primary_key=True)
    relation_class = Column(String, default='has')
    from_item_id = Column(Integer, ForeignKey('item.id'))
    to_item_id = Column(Integer, ForeignKey('item.id'))
    qty = Column(Float, default=1.0)

    from_item = relationship('Item', foreign_keys=['from_item_id'])
    to_item = relationship('Item', foreign_keys=['to_item_id'])


class Path(Base):
    __tablename__ = 'path'
    key = Column(String, unique=True)
    description =  Column(String)
    name = Column(String)
    is_a = Column(String)
    sequence = Column(Integer, default=0)
    from_node_id = Column(Integer, ForeignKey('node.id'), index=True)
    to_node_id = Column(Integer, ForeignKey('node.id'), index=True)
    resource_id = Column(Integer, ForeignKey('resource.id'), index=True)

    from_node = relationship('node', foreign_keys=['from_node_id'])
    to_node = relationship('node', foreign_keys=['to_node_id'])
    __mapper_args__ = {
        'polymorphic_on': is_a
    }

class Movement(Base):
    __tablename__ = 'movement'
    id = Column(Integer, primary_key=True)
    item_id = Column(ForeignKey('item.id'), nullable=False)
    from_node_id = Column(Integer, ForeignKey('resource.id'), index=True, nullable=False)
    to_node_id = Column(Integer, ForeignKey('resource.id'), index=True)
    path_id = Column(Integer, ForeignKey('path.id'))
    input_on = Column(DateTime, default=datetime.now)
    output_on = Column(DateTime)
    qty = Column(Float, default=1.0)

    from_node = relationship('Node', foreign_keys=['from_node_id'])
    to_node = relationship('Node', foreign_keys=['to_node_id'])
    item = relationship('Item')
    path = relationship('Path')


class Step(Base):
    __tablename__ = 'step'
    path_id


class DataAccessModule:
    def __init__(self, dal):
        self.dal = dal

    def move_item(self, item, to_node=Node, path=None):
        pass
