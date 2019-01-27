from sqlalchemy.orm import mapper, relationship, synonym
from sqlalchemy.orm.collections import attribute_mapped_collection
import quactrl.models.core as core
import quactrl.models.quality as qua
import quactrl.models.products as prod
import quactrl.models.operations as op
import quactrl.data.sqlalchemy.tables as tables
from quactrl.data.sqlalchemy.mappers.core import (resource_relationship,
                                                  item_relationship)

mapper(op.Location, inherits=core.Node)


mapper(op.Action, inherits=core.Flow,
       properties={
           'operation': synonym('parent'),
           'step': synonym('path')
       })


mapper(op.Operation, inherits=core.Flow,
       properties={
           'actions': relationship(op.Action, order_by='id',
                                   backref='operation')
       })


mapper(op.Route, inherits=core.Path,
       properties={
           'steps': relationship(op.Route, order_by='sequence',
                                 backref='route'),
           'source': synonym('from_node'),
           'destination': synonym('to_node')
       })


mapper(op.Step, inherits=core.Path)
