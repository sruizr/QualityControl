from sqlalchemy.orm import mapper, relationship, synonym
from sqlalchemy.orm.collections import attribute_mapped_collection
import quactrl.models.core as core
import quactrl.models.quality as qua
import quactrl.models.products as prod
import quactrl.data.sqlalchemy.tables as tables
from quactrl.data.sqlalchemy.mappers.core import resource_relationship, item_relationship


mapper(qua.Defect, inherits=core.Item,
       polymorphic_identity='defect',
       properties={
           'subject': item_relationship(qua.Subject, uselist=False),
       })


mapper(qua.Measurement, inherits=core.Item,
       polymorphic_identity='measurement',
       properties={
           'subject': item_relationship(qua.Subject, uselist=False),
       })


mapper(qua.Subject, inherits=core.Item,
       polymorphic_identity='subject',
       properties={
           'measurements': item_relationship(qua.Measurement),
           'defects': item_relationship(qua.Defect)
       }
)


mapper(qua.Mode, inherits=core.Resource,
       polymorphic_identity='mode')


mapper(qua.FailureMode, inherits=core.Resource,
       polymorphic_identity='failure_mode',
       properties={
           'characteristic': resource_relationship(prod.Characteristic,
                                                   uselist=False)
       }
)
