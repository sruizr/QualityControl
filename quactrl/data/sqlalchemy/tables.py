from datetime import datetime
from sqlalchemy import (Table, MetaData, Column, Integer, String, ForeignKey,
                        DateTime, Float)
from .types import JsonEncodedDict


metadata = MetaData()


node_table = Table('node', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('is_a', String(50)),
                   Column('key', String(15)),
                   Column('name', String(50)),
                   Column('description', String(255)))

node_link_table = Table('node_link', metadata,
                        Column('from_node', Integer, ForeignKey('node.id')),
                        Column('to_node', Integer, ForeignKey('node.id')),
                        Column('relation', String(100))
)

resource_table = Table('resource', metadata,
                       Column('id', Integer, primary_key=True),
                       Column('is_a', String(50)),
                       Column('key', String(15)),
                       Column('name', String(30)),
                       Column('description', String(200)),
                       Column('pars', JsonEncodedDict))


resource_link_table = Table('resource_link', metadata,
                            Column('from_resource', Integer,
                                   ForeignKey('resource.id')),
                            Column('to_resource', Integer,
                                   ForeignKey('resource.id')),
                            Column('relation', String(30)),
                            Column('qty', Float))


path_table = Table('path', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('is_a', String(50)),
                   Column('parent', Integer, ForeignKey('path.id')),
                   Column('prev', Integer, ForeignKey('path.id')),
                   Column('from_node', Integer, ForeignKey('node.id')),
                   Column('to_node', Integer, ForeignKey('node.id')),
                   Column('method_name', String(255)),
                   Column('role', Integer, ForeignKey('node.id')),
                   Column('pars', JsonEncodedDict))


flow_table = Table('flow', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('path_id', Integer, ForeignKey('path.id')),
                   Column('is_a', String(50)),
                   Column('responsible', Integer, ForeignKey('node.id')),
                   Column('started_on', DateTime, default=datetime.now),
                   Column('finished_on', DateTime),
                   Column('state', String(50)))


item_table = Table('item', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('resource_id', Integer, ForeignKey('resource.id')),
                   Column('is_a', String(50)),
                   Column('tracking', String(150)),
                   Column('pars', JsonEncodedDict))


token_table = Table(
    'token', metadata,
    Column('flow_id', Integer, primary_key=True),
    Column('item_id', Integer, ForeignKey('item.id'), index=True),
    Column('node_id', Integer, ForeignKey('node.id'), index=True),
    Column('qty', Float),
    Column('state', String(15))
)

item_link_table = Table('item_link', metadata,
                        Column('from_item', Integer, ForeignKey('item.id')),
                        Column('to_item', Integer, ForeignKey('item.id')),
                        Column('name', String(30)))
