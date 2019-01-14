from sqlalchemy import (Table, MetaData, Column, Integer, String, ForeignKey,
                        DateTime, Float)

metadata = MetaData()


node_table = Table('node', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('is_a', String(50)),
                   Column('key', String(15)),
                   Column('name', String(50)),
                   Column('description', String(255)))


resource_table = Table('resource', metadata,
                       Column('id', Integer, primary_key=True),
                       Column('is_a', String(50)),
                       Column('key', String(15)),
                       Column('name', String(30)),
                       Column('description', String(200)),
                       Column('pars', String(1000)))


resource_link_table = Table('resource_link', metadata,
                            Column('from_resource', Integer,
                                   ForeignKey('resource.id')),
                            Column('to_resource', Integer,
                                   ForeignKey('resource.id')),
                            Column('name', String(30)))


path_table = Table('path', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('is_a', String(30)),
                   Column('parent', Integer, ForeignKey('path.id')),
                   Column('sequence', Integer, default=0),
                   Column('from_node', Integer, ForeignKey('node.id')),
                   Column('to_node', Integer, ForeignKey('node.id')),
                   Column('method_name', String(255)),
                   Column('role', Integer, ForeignKey('node.id')),
                   Column('pars', String))


flow_table = Table('flow', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('path_id', Integer, ForeignKey('path.id')),
                   Column('is_a', String(30)),
                   Column('responsible', Integer, ForeignKey('node.id')),
                   Column('started_on', DateTime),
                   Column('finished_on', DateTime),
                   Column('state'))


item_table = Table('item', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('resource_id', Integer, ForeignKey('resource.id')),
                   Column('is_a', String(30)),
                   Column('pars', String(1000)))


token_table = Table('token', metadata,
                    Column('flow_id', Integer, primary_key=True),
                    Column('item_id', Integer, ForeignKey('item.id')),
                    Column('node_id', Integer, ForeignKey('node.id')),
                    Column('qty', Float),
                    Column('state', String(15)))


item_link_table = Table('resource_link', metadata,
                        Column('from_item', Integer, ForeignKey('item.id')),
                        Column('to_item', Integer, ForeignKey('item.id')),
                        Column('name', String(30)))
