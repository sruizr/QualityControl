from sqlalchemy.exc import IntegrityError
import quactrl.domain.base as b
import quactrl.domain.nodes as n
import quactrl.domain.resources as r
import quactrl.domain.paths as p
import quactrl.domain.items as i
from quactrl.managers import Manager

"""Class mapping for crud operations"""
CLASSES = {
    'person': n.Person,
    'role': n.Role,
    'location': n.Location,
    'part': i.Part,
    'form': r.Form,
    'part_model': r.PartModel,
    'control_plan': p.ControlPlan,
    'control': p.Control,
    'operation': p.Operation,
    'characteristic': r.Characteristic,
    'requirement': r.Requirement,
    'part_group': r.PartGroup,
    'failure': r.Failure,
    'failure_mode': r.FailureMode,
    'device_group': r.DeviceGroup
}


RELATIONSHIPS = {
    'roles': n.Role,
    'members': n.Person,
    'failures': r.Failure,
    'requirements': r.Requirement,
    'components': r.Composition,
}


class Crud(Manager):
    """CRUD basic operations on domain """
    def __init__(self):
        super().__init__()

    def create(self, class_name, **fields):
        session = self.dal.Session()
        if 'type' in fields.keys():
            type_ = fields.pop('type')
        else:
            type_ = class_name

        ObjClass = CLASSES[type_]


        obj = ObjClass()
        self._update_fields(obj, fields)
        session.add(obj)
        session.commit()

        return obj

    def _create(self):
        pass

    def delete(self, class_name, id):
        session = self.dal.Session()
        session.query(CLASSES[class_name]).filter_by(id=id).delete()
        session.commit()

    def read(self, class_name, **filters):
        session = self.dal.Session()
        results = session.query(CLASSES[class_name]).filter_by(**filters).all()
        if len(results) == 1:
            return results[0]
        else:
            return results

    def update(self, class_name, id,  **fields):
        session = self.dal.Session()
        obj = session.query(CLASSES[class_name]).filter_by(id=id).one_or_none()
        self._update_fields(obj, fields)

        session.commit()

    def _update_fields(self, obj, fields):
        for attr, value in fields.items():
            if attr in RELATIONSHIPS.keys():  #  Fields with domain objects
                self._update_domain_field(obj, attr, value)

            elif attr == 'pars':  # pars field
                if obj.pars is None:
                    obj.pars = b.Pars()
                for key, _value in value.items():
                    obj.pars[key] = _value
            else:  # Primitive field
                if hasattr(obj, attr):
                    setattr(obj, attr, value)
                else:
                    raise Exception('Not correct field')

    def _update_domain_field(self, obj, attr, value):
        DomainClass = RELATIONSHIPS[attr]

        query = self.dal.Session().query(DomainClass)

        if self._is_multiple_object_field(value):  # Mapping to several domain objects
            attr_field = getattr(obj, attr)
            if type(value) is list:
                children = []

                for value_ in value:
                    if type(value_) is str:  # Objects by key
                        child = query.filter(DomainClass.key==value_).one()
                    elif type(value_) is int:  # Objects by id
                        child = query.filter(DomainClass.id==value_).one()
                    elif type(value_) is dict:  # Object definitions
                        type_ = value_.pop('type')
                        if type_:
                            ObjClass = CLASSES[type_]
                        else:
                            ObjClass = DomainClass
                        child = ObjClass()
                        self._update_fields(child, value_)
                    children.append(child)

                for child in children:
                    attr_field.append(child)
        else:  # Mapping to one object
            if type(value) is str:  #  Defined by key
                value = query.filter(DomainClass.key == value).one_or_none()
            elif type(value) is int:   # One to one by id
                value = query.filter(DomainClass.id == value).one_or_none()
            elif type(value) is dict:  # Create a new one
                type_ = value.pop('type')
                value = self.create(type_, **value)

            setattr(obj, attr, value)


    def _is_multiple_object_field(self, value):
        return type(value) is list or (
            type(value) is dict and 'type' not in value.keys()
        )
