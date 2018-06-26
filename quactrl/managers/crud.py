from sqlalchemy.exc import IntegrityError
import quactrl.domain.base as b
import quactrl.domain.nodes as n
import quactrl.domain.resources as r
import quactrl.domain.paths as p
import quactrl.domain.items as i
import quactrl.domain.flows as f
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
    'group': r.Group,
    'failure': r.Failure,
    'failure_mode': r.FailureMode,
    'device_model': r.DeviceModel,
    'process': r.Process,
    'control_plan': p.ControlPlan,
    'reporting': p.Reporting,
    'device': i.Device
}


RELATIONSHIPS = {
    'roles': n.Role,
    'persons': n.Person,
    'failures': r.Failure,
    'requirements': r.Requirement,
    'components': r.Composition,
    'characteristic': r.Characteristic,
    'members': r.Clasification,
    'member': r.Resource,
    'group': r.Group,
    'groups': r.Clasification,
    'part_model': r.Resource,
    'process': r.Process,
    'role': n.Role,
    'steps': p.Operation,
    'from_node': n.Location,
    'to_node': n.Location,
    'form': r.Form,
    'device_model': r.DeviceModel
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
            elif attr == 'create':
                responsible_key = value['responsible']
                node_key = value['location']
                qty = value.get('qty', 1.0)
                self._create_token(obj, node_key, responsible_key, qty)
            else:  # Primitive field
                if hasattr(obj, attr):
                    try:
                        setattr(obj, attr, value)
                    except:
                        import pdb; pdb.set_trace()
                else:
                    raise Exception(
                        'Not correct field "{}" for class "{}" with key {}'.format(
                            attr, obj.__class__.__name__, getattr(obj, 'key', None)))

    def _update_domain_field(self, obj, attr, value):
        DomainClass = RELATIONSHIPS[attr]

        query = self.dal.Session().query(DomainClass)

        if self._is_multiple_object_field(value):  # Mapping to several domain objects
            attr_field = getattr(obj, attr)
            if type(value) is list:
                children = []

                for value_ in value:
                    if type(value_) is str:  # Objects by key
                        try:
                            child = query.filter(DomainClass.key==value_).one()
                        except Exception as e:
                            print('Not found key: {}'.format(value))
                            raise e
                    elif type(value_) is int:  # Objects by id
                        try:
                            child = query.filter(DomainClass.id==value_).one()
                        except Exception as e:
                            print('Not found key: {}'.format(value))
                            raise e
                    elif type(value_) is dict:  # Object definitions
                        type_ = value_.pop('type', None)
                        if type_:
                            ObjClass = CLASSES[type_]
                        else:
                            ObjClass = DomainClass
                        child = ObjClass()
                        self._update_fields(child, value_)
                    children.append(child)

                for child in children:
                    if attr_field is None:
                        import pdb; pdb.set_trace()

                    attr_field.append(child)
        else:  # Mapping to one object
            if type(value) is str:  #  Defined by key
                try:
                    value = query.filter(DomainClass.key == value).one()
                except Exception as e:
                    print('Not found key: {}'.format(value))
                    raise e
            elif type(value) is int:   # One to one by id
                try:
                    value = query.filter(DomainClass.id == value).one()
                except Exception as e:
                    print('Not found key: {}'.format(value))
                    raise e
            elif type(value) is dict:  # Create a new one
                type_ = value.pop('type', None)
                if type_:
                    ObjClass = CLASSES[type_]
                else:
                    ObjClass = DomainClass
                value_ = value
                value = ObjClass()
                self._update_fields(value, value_)

            setattr(obj, attr, value)

    def _create_token(self, item, location_key, responsible_key, qty=1.0):
        session = self.dal.Session()
        try:
            responsible = session.query(n.Person).filter(
                n.Person.key == responsible_key).one()
        except:
            import pdb; pdb.set_trace()

        location = session.query(b.Node).filter(
            b.Node.key == location_key).one()

        creation = f.Creation(responsible)
        item.qty = qty
        creation.run(location, item)

    def _is_multiple_object_field(self, value):
        return type(value) is list

    def _get_obj_by_key(self, ClassObj, key):
        session = self.dal.Session()
        try:
            return session.query(ClassObj).filter(ClassObj.key == key).one()
        except Exception as e:
            print('Not found key: {}'.format(key))
            raise e

    def _get_obj_by_id(self, ClassObj, id):
        session = self.dal.Session()
        try:
            return session.query(ClassObj).filter(ClassObj.id == id).one()
        except Exception as e:
            print('Not found id: {}'.format(id))
            raise e
