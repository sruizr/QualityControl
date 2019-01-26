from sqlalchemy.orm import mapper, relationship
import quactrl.data.sqlalchemy.tables as tables
import quactrl.models.hhrr as hhrr


mapper(hhrr.Person, tables.node,
       inherits=hhrr.Node, polymorphic_identity='person',
       properties={
           'roles': relationship(
               hhrr.Role,
               secondary=tables.node_link,
               primaryjoin=(
                   tables.node.c.id == tables.node_link.c.from_node_id
               ),
               secondaryjoin=(
                   tables.node.c.id == tables.node_link.c.to_node_id
               ),
               backref='persons'
           )
       },)


mapper(hhrr.Role, tables.node,
       inherits=hhrr.Node, polymorphic_identity='role')
