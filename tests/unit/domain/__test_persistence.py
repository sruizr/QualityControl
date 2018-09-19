from sqlalchemy import inspect
from tests.domain import EmptyDataTest
from quactrl.domain.nodes import Person

class A_DataAccessLayer:
    def should_manage_scoped_session(self):
        pass

    def should_connect(self):
        pass

# def load_data(dal):
#     session = dal.Session()
#     operation = Operation()
#     wip = Location('wip')
#     warehouse = Location('warehouse')
#     quality = Node('qua')

#     operation.method_name = 'final_test'
#     operation.from_node = wip
#     operation.to_node = warehouse

#     control_plan = ControlPlan()
#     control_plan.from_node = wip
#     control_plan.to_node = quality

#     operation.children.append(control_plan)
#     operator = Person('000')

#     control_1 = Control()
#     control_2 = Control()
#     control_2.sequence = 10
#     control_1.parent = control_plan
#     control_2.parent = control_plan

#     session.add_all([operation, operator, control_plan, control_1, control_2])
#     session.commit()
