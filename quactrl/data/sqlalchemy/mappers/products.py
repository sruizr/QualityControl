from sqlalchemy.orm import mapper, relationship, synonym
from sqlalchemy.orm.collections import attribute_mapped_collection
import quactrl.models.products as products
import quactrl.models.core as core
import quactrl.models.quality as quality
import quactrl.data.sqlalchemy.tables as tables


mapper(products.PartGroup, inherits=core.Resource,
       polymorphic_identity='part_group',
       properties={
           'models': relationship(
               products.PartModel,
               secondary=tables.resource_link,
               primaryjoin=(
                   tables.resource.c.id == tables.resource_link.c.from_resource_id
               ),
               secondaryjoin=(
                   tables.resource.c.id == tables.resource_link.c.to_resource_id
               ),
               backref='groups'
           )
       })


mapper(products.PartModel, inherits=products.PartGroup,
       polymorphic_identity='part_model')


mapper(products.Requirement, inherits=core.Resource,
       polymorphic_identity='requirement',
       properties={
           'characteristic': relationship(
               products.Characteristic,
               secondary=tables.resource_link,
               primaryjoin=(
                   tables.resource.c.id == tables.resource_link.c.from_resource_id
               ),
               secondaryjoin=(
                   tables.resource.c.id == tables.resource_link.c.to_resource_id
               ),
               uselist=False),
           'requirements': relationship(
               products.Requirement,
               secondary=tables.resource_link,
               primaryjoin=(
                   tables.resource.c.id == tables.resource_link.c.from_resource_id
               ),
               secondaryjoin=(
                   tables.resource.c.id == tables.resource_link.c.to_resource_id
               ),
               collection_class=attribute_mapped_collection('key')),
           'specs': synonym('pars')
       }
)


mapper(products.Characteristic, inherits=core.Resource,
       polymorphic_identity='characteristic',
       properties={
           'element': relationship(
               products.Element,
               secondary=tables.resource_link,
               primaryjoin=(
                   tables.resource.c.id == tables.resource_link.c.from_resource_id
               ),
               secondaryjoin=(
                   tables.resource.c.id == tables.resource_link.c.to_resource_id
               ),
               uselist=False),
           'attribute': relationship(
               products.Attribute,

               secondary=tables.resource_link,
primaryjoin=(
                   tables.resource.c.id == tables.resource_link.c.from_resource_id
               ),
               secondaryjoin=(
                   tables.resource.c.id == tables.resource_link.c.to_resource_id
               ),
               uselist=False),
           'failure_modes': relationship(
               quality.FailureMode,
               secondary=tables.resource_link,
               primaryjoin=(
                   tables.resource.c.id == tables.resource_link.c.from_resource_id
               ),
               secondaryjoin=(
                   tables.resource.c.id == tables.resource_link.c.to_resource_id
               ),
               collection_class=attribute_mapped_collection('key'))
       })


mapper(products.Element, inherits=core.Resource,
       polymorphic_identity='element')


mapper(products.Attribute, inherits=core.Resource,
       polymorphic_identity='attribute')
