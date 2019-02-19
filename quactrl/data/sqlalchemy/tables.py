from datetime import datetime
from sqlalchemy import (Table, MetaData, Column, Integer, String, ForeignKey,
                        DateTime, Float, Boolean, UniqueConstraint)
from .types import JsonEncodedDict
from quactrl.data.sqlalchemy import metadata


node = Table('node', metadata,
             Column('id', Integer, primary_key=True),
             Column('is_a', String(50)),
             Column('key', String(25)),
             Column('name', String(50)),
             Column('description', String(255)),
             UniqueConstraint('key', 'is_a', name='uix_node')
)


node_link = Table('node_link', metadata,
                  Column('from_node_id', Integer, ForeignKey('node.id')),
                  Column('to_node_id', Integer, ForeignKey('node.id')))


resource = Table('resource', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('is_a', String(50)),
                 Column('key', String(25)),
                 Column('name', String(30)),
                 Column('description', String(200)),
                 Column('pars', JsonEncodedDict),
                 UniqueConstraint('key', 'is_a', name='uix_resource')
)


resource_link = Table('resource_link', metadata,
                      Column('from_resource_id', Integer,
                             ForeignKey('resource.id')),
                      Column('to_resource_id', Integer,
                             ForeignKey('resource.id')))


path_resource = Table('path_resource', metadata,
                     Column('id', Integer, primary_key=True),
                     Column('path_id', Integer, ForeignKey('path.id')),
                     Column('resource_id', Integer, ForeignKey('resource.id')))


path = Table('path', metadata,
             Column('id', Integer, primary_key=True),
             Column('is_a', String(50)),
             Column('parent_id', Integer, ForeignKey('path.id')),
             Column('sequence', Integer),
             Column('from_node_id', Integer, ForeignKey('node.id')),
             Column('to_node_id', Integer, ForeignKey('node.id')),
             Column('role_id', Integer, ForeignKey('node.id')),
             Column('method_name', String(255)),
             Column('method_pars', JsonEncodedDict))


flow = Table('flow', metadata,
             Column('id', Integer, primary_key=True),
             Column('path_id', Integer, ForeignKey('path.id')),
             Column('is_a', String(50)),
             Column('parent_id', Integer, ForeignKey('flow.id')),
             Column('responsible_id', Integer, ForeignKey('node.id')),
             Column('started_on', DateTime, default=datetime.now),
             Column('finished_on', DateTime),
             Column('state', String(50)))


item = Table('item', metadata,
             Column('id', Integer, primary_key=True),
             Column('resource_id', Integer, ForeignKey('resource.id')),
             Column('is_a', String(50)),
             Column('tracking', String(150)),
             Column('pars', JsonEncodedDict),
             UniqueConstraint('resource_id', 'tracking', name='uix_item')
)


token = Table(
    'token', metadata,
    Column('id', Integer, primary_key=True),
    Column('flow_id', Integer, ForeignKey('flow.id')),
    Column('item_id', Integer, ForeignKey('item.id'), index=True),
    Column('node_id', Integer, ForeignKey('node.id'), index=True),
    Column('qty', Float),
    Column('current', Boolean)
)


item_link = Table('item_link', metadata,
                  Column('from_item_id', Integer, ForeignKey('item.id')),
                  Column('to_item_id', Integer, ForeignKey('item.id')))
