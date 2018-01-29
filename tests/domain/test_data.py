from quactrl.domain.data import DataAccessLayer
from quactrl.domain.erp import Node
from quactrl.domain.plan import Process
from quactrl.domain.check import Control, ControlPlan
from quactrl.domain.do import Location, Person

class A_DataAccessLayer:
    pass


class OnMemoryTest:
    dal = DataAccessLayer()
    dal.db_init('sqlite:///:memory:', False)
    dal.prepare_db()

    def setup_method(self, method):
        self._transaction = self.dal.connection.begin()
        self.session = self.dal.Session(bind=self.dal.connection)

    def teardown_method(self, method):
        # self.session.rollback()
        self._transaction.rollback()
        self.session.close()

def load_data(dal):
    session = dal.Session()
    process = Process()
    wip = Location('wip')
    warehouse = Location('warehouse')
    quality = Node('qua')

    process.method_name = 'final_test'
    process.from_node = wip
    process.to_node = warehouse

    control_plan = ControlPlan()
    control_plan.from_node = wip
    control_plan.to_node = quality

    process.children.append(control_plan)
    operator = Person('000')

    control_1 = Control()
    control_2 = Control()
    control_2.sequence = 10
    control_1.parent = control_plan
    control_2.parent = control_plan

    session.add_all([process, operator, control_plan, control_1, control_2])
    session.commit()
