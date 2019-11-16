from sqlalchemy.orm import mapper, relationship, synonym
from sqlalchemy.orm.collections import attribute_mapped_collection
import quactrl.models.core as core
import quactrl.models.quality as qua
import quactrl.models.products as prod
import quactrl.models.operations as op
import quactrl.data.sqlalchemy.tables as tables
from quactrl.data.sqlalchemy.mappers.core import (resource_relationship,
                                                  item_relationship,
                                                  node_relationship)

mapper(op.Location, inherits=core.Node,
       polymorphic_identity='location',
       properties={
           'sub_locations': node_relationship(
               op.Location,
               collection_class=attribute_mapped_collection('key')
           )}
)



mapper(op.Action, inherits=core.Flow,
       polymorphic_identity='action',
       properties={
           'operation': synonym('parent'),
           'step': synonym('path')
       })


mapper(op.Operation, inherits=core.Flow,
       polymorphic_identity='operation',
       properties={
           'actions': synonym('subflows'),
           'route': synonym('path')
       })


mapper(op.Route, inherits=core.Path,
       polymorphic_identity='route',
       properties={
           'steps': synonym('subpaths'),
           'source': synonym('from_node'),
           'destination': synonym('to_node'),
           'outputs': relationship(prod.PartGroup,
                                   secondary=tables.path_resource)

       })


mapper(op.Step, inherits=core.Path,
       polymorphic_identity='step',
       properties={
           'source': synonym('from_node'),
           'destination': synonym('to_node')
       })
