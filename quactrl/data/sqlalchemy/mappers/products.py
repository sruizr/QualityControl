from sqlalchemy.orm import mapper, relationship, synonym
import quactrl.models.products as products
import quactrl.models.core as core
import quactrl.models.quality as quality
import quactrl.data.sqlalchemy.tables as tables


mapper(products.PartGroup, tables.resource,
       inhterits=core.Resource, polymorphic_identity='part_group',
       properties={
           'part_models': relationship(
               products.PartModel,
               secondary=tables.resource_link,
               primaryjoin=(
                   tables.resource.c.id == tables.resource_link.c.from_resource
               ),
               secondaryjoin=(
                   tables.resource.c.id == tables.resource_link.c.to_resource
               ),
               backref='groups'
           )
       })


mapper(products.PartModel, tables.resource,
       inherits=products.PartGroup, polymorphic_identity='part_model')


mapper(products.Requirement, tables.resource,
       inherits=core.Resource, polymorphic_identity='requirement',
       properties={
           'characteristic': relationship(products.Characteristic,
                                          uselist=False),
           'specs': synonym('pars'),
           'requirements': association_proxy()
       }
)


mapper(products.Characteristic, tables.resource,
       inherits=core.Resource, polymorphic_identity='characteristic',
       properties={
           'element': relationship(products.Element,
                                   secondary=tables.resource_link,
                                   uselist=False),
           'attribute': relationship(products.Attribute,
                                     secondary=tables.resource_link,
                                     uselist=False),
           'failure_modes': relationship(quality.modes,
                                         secondary=tables.resource_link)
       })


mapper(products.Element, tables.resource,
       inherits=core.Resource, polymorphic_identity='element')


mapper(products.Attribute, tables.resource,
       inherits=core.Resource, polymorphic_identity='attribute')
