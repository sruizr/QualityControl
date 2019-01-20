from sqlalchemy.orm import mapper
import quactrl.models.core as core


node_mapper = mapper('node', core.Node)


resource_mapper = mapper('resource', core.Resource)


resource_link_mapper = mapper('resource_link', core.ResourceLink)


item_mapper = mapper('item', core.Item)


token_mapper = mapper('token', core.Token)


unitary_item_mapper = mapper('item', core.UnitaryItem)


flow_mapper = mapper('flow', core.Flow)


item_link_mapper = mapper('item_link', core.ItemLink)


path_mapper = mapper('path', core.Path)
