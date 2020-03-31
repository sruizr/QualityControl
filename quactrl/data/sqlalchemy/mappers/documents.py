from sqlalchemy.orm import mapper, synonym, backref
import quactrl.models.core as core
import quactrl.models.operations as op
import quactrl.models.documents as doc
from quactrl.data.sqlalchemy.mappers.core import node_relationship


mapper(doc.Directory, inherits=core.Node,
       polymorphic_identity='directory',
       properties={
           'directories': node_relationship(
               doc.Directory,
               backref=backref('parent', uselist=False)
           )
       })


mapper(doc.Document, inherits=core.Item,
       polymorphic_identity='pdf_doc',
       properties={
           'form': synonym('resource')
       })


mapper(doc.Form, inherits=core.Resource,
       polymorphic_identity='form')


mapper(doc.AdmintStep, inherits=op.Step,
       polymorphic_identity='admin_step')


mapper(doc.AdminTask, inherits=op.Acttion,
       polymorphic_identity='task',
       properties={
           'operation': synonym('parent'),
           'step': synonym('path')
       })
