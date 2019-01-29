from sqlalchemy.orm import mapper, synonym, relationship, backref
import quactrl.models.core as core
import quactrl.models.quality as qua
import quactrl.models.products as prod
import quactrl.models.operations as op
import quactrl.data.sqlalchemy.tables as tables
from quactrl.data.sqlalchemy.mappers.core import (resource_relationship,
                                                  item_relationship)


mapper(qua.Defect, inherits=core.Item,
       polymorphic_identity='defect',
       properties={
           'failure_mode': synonym('resource')
       })


mapper(qua.Measurement, inherits=core.Item,
       polymorphic_identity='measurement',
       properties={
           'characteristic': synonym('resource')
       })


mapper(qua.Subject, inherits=core.UnitaryItem,
       polymorphic_identity='subject',
       properties={
           'measurements': item_relationship(qua.Measurement,
                                             backref=backref('subject', uselist=False)),
           'defects': item_relationship(qua.Defect,
                                        backref=backref('subject', uselist=False))
       })


mapper(prod.Part, inherits=qua.Subject,
       polymorphic_identity='part',
       properties={
           'serial_number': synonym('tracking'),
           'model': synonym('resource')
       })


mapper(qua.Mode, inherits=core.Resource,
       polymorphic_identity='mode')


mapper(qua.FailureMode, inherits=core.Resource,
       polymorphic_identity='failure_mode',
       properties={
           'characteristic': resource_relationship(prod.Characteristic,
                                                   uselist=False),
           'mode': resource_relationship(qua.Mode, uselist=False)
       })


mapper(qua.Check, inherits=op.Action,
       polymorphic_identity='check',
       properties={
           'test': synonym('parent')
       }
)


mapper(qua.Test, inherits=op.Operation,
       polymorphic_identity='test',
       properties={
           'control_plan': synonym('path')
       }
)


mapper(qua.ControlPlan, inherits=op.Route,
       polymorphic_identity='control_plan',
)


mapper(qua.Control, inherits=op.Step,
       polymorphic_identity='control',
       properties={
           'control_plan': synonym('parent'),
           'requirement': relationship(prod.Requirement,
                                       secondary=tables.path_resource,
                                       uselist=False)
       })
