from datetime import datetime
from sqlalchemy import create_engine, ForeignKey, Column, UniqueConstraint
from sqlalchemy.types import (
    String, Integer, DateTime, DECIMAL
    )
from sqlalchemy.orm import sessionmaker, backref, relationship
from quactrl.entities import Base


class Model(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

    def __repr__(self):
        identification = '#{} - '.format(self.id)
        return identification + str(self)


class Resource(Model):
    __tablename__ = 'resource'
    key = Column(String)
    is_a = Column(String)
    name = Column(String)
    role = Column(String)
    description = Column(String)
    parameters = Column(String)
    __mapper_args__ = {
        'polymorphic_identity': 'resource',
        'polymorphic_on': is_a
    }


class Node(Resource):
    __mapper_args__ = {
        'polymorphic_identity': 'node'
    }


class Item(Model):
    __tablename__ = 'item'
    resource_id = Column(ForeignKey('resource.id'))
    resource = relationship("Resource")
    tracking = Column(String)
    qty = Column(Integer)


class Movement(Model):
    __tablename__ = 'movement'
    item_id = Column(ForeignKey('item.id'))
    from_node_id = Column(ForeignKey('resource.id'))
    to_node_id = Column(ForeignKey('resource.id'))
    input_on = Column(DateTime, default=datetime.now)
    output_on = Column(DateTime)
    from_node = relationship()
    to_node = relationship()
    item = relationship()
