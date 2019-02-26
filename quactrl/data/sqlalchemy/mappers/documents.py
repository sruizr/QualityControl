from sqlalchemy.orm import mapper, relationship, synonym, backref
import quactrl.models.core as core
import quactrl.models.operations as op
import quactrl.models.documents as doc
from quactrl.data.sqlalchemy.mappers.core import (resource_relationship, node_relationship)


mapper(doc.Directory, inherits=core.Node,
       polymorphic_identity='directory',
       properties={
           'directories': node_relationship(
               doc.Directory,
               backref=backref('parent', uselist=False)
           )
       }
)


mapper(doc.Document, inherits=core.Item,
       polymorphic_identity='pdf_doc',
       properties={
           'form': synonym('resource')
       }
)


mapper(doc.Form, inherits=core.Resource,
       polymorphic_identity='form'
)


mapper(doc.PrintStep, inherits=op.Step,
       polymorphic_identity='print')


mapper(doc.FillStep, inherits=op.Step,
        polymorphic_identity='fill')


mapper(doc.Fill, inherits=core.Flow,
       polymorphic_identity='fill',
       properties={
           'operation': synonym('parent')
       })


mapper(doc.Print, inherits=op.Flow,
       polymorphic_identity='print',
       properties={
           'operation': synonym('parent')
       })
