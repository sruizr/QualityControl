import quactrl.domain.nodes as nodes
import quactrl.domain.resources as resources
import quactrl.domain.paths as paths
import quactrl.domain.items as items
import quactrl.domain.flows as flows
from quactrl.managers import Manager

"""Class mapping for crud operations"""
CLASSES = {
    'person': nodes.Person,
    'group': nodes.Group,
    'location': nodes.Location,
    'part': items.Part,
    'part_model': resources.PartModel,
    'control_plan': paths.ControlPlan,
    'control': paths.Control,
    'check': flows.Check,
    'test': flows.Test
}


class Crud(Manager):
    """CRUD basic operations on domain """
    def __init__(self):
        super().__init__()

    def create(self, class_name, **fields):
        session = self.dal.Session()
        obj = CLASSES[class_name](**fields)
        session.add(obj)
        session.commit()
        return obj

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

        for key, value in fields.items():
            setattr(obj, key, value)
        session.commit()
