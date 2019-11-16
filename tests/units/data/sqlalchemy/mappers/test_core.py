from quactrl.data.sqlalchemy.mappers import core
import quactrl.models.core as c
from . import TestMapper


class A_CoreModule(TestMapper):
    def should_link_flows(self):
        responsible = c.Node(key='resp')
        flow = c.Flow(responsible)
        sub_flow = c.Flow(None)

        sub_flow.parent = flow

        session = self.Session()
        session.add(flow)
        session.commit()

        # New session\
        session = self.Session()
        flow = session.query(c.Flow).first()
        assert flow.subflows[0].responsible is None
        assert flow.responsible.key == 'resp'

    def should_link_paths(self):
        pass
