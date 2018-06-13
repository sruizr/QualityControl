from sqlalchemy.exc import IntegrityError
import quactrl.domain.nodes as n
import quactrl.domain.resources as resources
import quactrl.domain.paths as paths
import quactrl.domain.items as items
import quactrl.domain.flows as flows
from quactrl.managers import Manager

"""Class mapping for crud operations"""
CLASSES = {
    'person': n.Person,
    'role': n.Role,
    'location': n.Location,
    'part': items.Part,
    'part_model': resources.PartModel,
    'control_plan': paths.ControlPlan,
    'control': paths.Control
}

RELATIONSHIPS = {
    'roles': n.Role,
    'members': n.Person

}
class Crud(Manager):
    """CRUD basic operations on domain """
    def __init__(self):
        super().__init__()

    def create(self, class_name, **fields):
        session = self.dal.Session()
        ObjClass = CLASSES[class_name]

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
        return results

    def update(self, class_name, id,  **fields):
        session = self.dal.Session()
        obj = session.query(CLASSES[class_name]).filter_by(id=id).one_or_none()
        self._update_fields(obj, fields)

        session.commit()

    def _update_fields(self, obj, fields):
        for att, value in fields.items():
            if att in RELATIONSHIPS.keys():  #  Fields with domain objects
                if type(value) is list: # Association proxy
                    if type(value[0]) is str: # List of already existing domain objects by  keys
                        pass
                    if type(value[0]) is int: # List of already existing domain objects by  ids
                        pass
                    elif type(value[0]) is dict: # New child object
                        pass
                elif type(value) is dict:  # A dict proxy
                    pass
                elif type(value) is str:  #  Key access for obj
                    pass
            else:
                # Primitive
                if hasattr(obj, att):
                    obj.att = value
                else:
                    raise Exception('Not correct field')
