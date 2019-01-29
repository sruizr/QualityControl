from . import TestMapper
from quactrl.data.sqlalchemy.mappers import core, products, operations, quality
import quactrl.models.products as prd
import quactrl.models.quality as qua
import quactrl.models.operations as op


class A_OperationMapper(TestMapper):
    def should_map_location(self):
        session = self.Session()
        location = op.Location('loc')
        session.add(location)
        session.commit()

        session = self.Session()
        loc = session.query(op.Location).first()
        assert loc.key == 'loc'

    def should_link_operations_with_actions(self):
        operation = op.Operation(None, None)

        # action = op.Action(operation, None)

        # session = self.Session()
        # session.add(operation)

        # session.commit()
