from quactrl.domain.check import Check, Test, Control, ControlPlan, Measure, Defect
from quactrl.domain.erp import Resource, Path, Item, Node, PathResource
from tests.domain.test_data import OnMemoryTest



class A_Check(OnMemoryTest):
    def setup_method(self, method):
        super().setup_method(method)
        part_model = Resource('part_model')
        control_plan = ControlPlan()
        control_plan.add_resource(part_model)

        user = Node('123')
        test = Test(control_plan, user)
        checked_item = Item(Resource('item'))

        control = Control()
        control.from_node = Node('origin2')
        control.characteristic = Resource('char')

        self.check = Check(test, control, checked_item)
        self.checked_item = checked_item

    def should_be_created(self):

        self.session.add(self.check)
        self.session.commit()

        assert self.check.id is not None
        assert self.check.is_a == 'check'
        assert self.check.destinations[0].to_item == self.checked_item

    def should_be_closed(self):
        self.check.close()

        self.session.add(self.check)
        self.session.commit()

        assert self.check.state == 'ok'

        self.check.defects.append(None)
        self.check.close()

        assert self.check.state == 'nok'

    def should_be_cancelled(self):
        self.check.cancel()

        self.session.add(self.check)
        self.session.commit()

        self.check.state == 'cancelled'

    def should_add_measures(self):
        characteristic = Resource('')
        value = 5.0

        self.check.add_measure(characteristic, value)

        self.session.add(self.check)
        self.session.commit()

        measure = self.check.measures[-1]
        assert measure.movements[-1].qty == value
        assert self.check.destinations[-1].to_item == measure


    def should_add_defects(self):
        failure_mode = Resource('')

        self.check.add_defect(failure_mode)

        self.session.add(self.check)
        self.session.commit()

        defect = self.check.defects[-1]
        assert self.check.destinations[-1].to_item == defect

    def should_load_fields(self):
        failure_mode = Resource('mode-char')
        characteristic = Resource('char1')
        self.check.add_defect(failure_mode)
        self.check.add_measure(characteristic, 0.2)

        self.session.add(self.check)
        self.session.commit()

        del(self.check)

        check = self.session.query(Check).first()

        assert check.item
        assert check.measures
        assert check.defects
        assert check.measures[0].value == 0.2

class A_Test(OnMemoryTest):
    def should_be_created(self):

        control_plan = Path()
        user = Node('')
        test = Test(control_plan, user)

        self.session.add(test)
        self.session.commit()


        assert test.id is not None
        assert test.is_a == 'test'


# class A_Measure(OnMemoryTest):
#     def
