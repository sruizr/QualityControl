from sqlalchemy.orm import mapper, relationship
import quactrl.models.core as core
import quactrl.data.sqlalchemy.tables as tables


def resource_relationship(*args, **kwargs):
    mapping = {
        'secondary': tables.resource_link,
        'primaryjoin': (
            tables.resource.c.id == tables.resource_link.c.from_resource_id
        ),
        'secondaryjoin': (
            tables.resource.c.id == tables.resource_link.c.to_resource_id
        )
    }
    kwargs.update(mapping)
    return relationship(*args, **kwargs)


def item_relationship(*args, **kwargs):
    mapping = {
        'secondary': tables.item_link,
        'primaryjoin': (
            tables.item.c.id == tables.item_link.c.from_item_id
        ),
        'secondaryjoin': (
            tables.item.c.id == tables.item_link.c.to_item_id
        )
    }
    kwargs.update(mapping)
    return relationship(*args, **kwargs)


mapper(core.Node, tables.node,
       polymorphic_on=tables.node.c.is_a,
       polymorphic_identity='node'
)


mapper(core.Resource, tables.resource,
       polymorphic_on=tables.resource.c.is_a,
       polymorphic_identity='resource'
)


mapper(core.Path, tables.path,
       polymorphic_on=tables.path.c.is_a)


mapper(core.Item, tables.item,
       polymorphic_on=tables.item.c.is_a,
       properties={
           'resource': relationship(core.Resource),
           'tokens': relationship(core.Token)
       })


mapper(core.Flow, tables.flow,
       polymorphic_on=tables.flow.c.is_a,
       properties={
           'responsible': relationship(core.Node),
           'path': relationship(core.Path),
           'parent': relationship(core.Flow)
       })


mapper(core.Token, tables.token,
       properties={
           'item': relationship(core.Item),
           'node': relationship(core.Node),
           'flow': relationship(core.Flow)
       })
