from sqlalchemy.orm import mapper
import quactrl.models.core as core
import quactrl.data.sqlalchemy.tables as tables


mapper(core.Node, tables.node,
       polymorphic_on=tables.node.c.is_a)


mapper(core.Resource, tables.resource,
       polymorphic_on=tables.resource.c.is_a)


mapper(core.Node, tables.node,
       polymorphic_on=tables.node.c.is_a)


mapper(core.Node, tables.node,
       polymorphic_on=tables.node.c.is_a)


mapper(core.Path, tables.path,
       polymorphic_on=tables.path.c.is_a)


mapper(core.Item, tables.item,
       polymorphic_on=tables.item.c.is_a)


mapper(core.Flow, tables.flow,
       polymorphic_on=tables.item.c.is_a)


mapper(core.Token, tables.token)
