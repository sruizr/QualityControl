from quactrl.domain.do import Person, Device, Group, Location, Part, Generator
from quactrl.domain.base import Flow
from quactrl.domain.plan import (
    DeviceModel, PartModel, Characteristic, Operation
    )
from quactrl.domain.check import ControlPlan, Control


class Filler:

    def __init__(self, dal):
        self.dal = dal

    def load(self):
        session = self.dal.Session()

        src = Location('src', 'Origin of all generators')
        wip = Location('wip', 'Origin of test')

        des = Location('des', 'Destination of testd parts')
        locations = [src, wip, des]

        person = Person('007', 'James Bond')

        device_model = DeviceModel('ms',
                                   'Measure system to be used by the check',
                                   pars={}
        )
        # device = Device(
        #     device_model, '00000',
        #
        # )

        part_model = PartModel(
            'partnumber', 'Part description',
            pars={'class_name': 'tests.integration.stuff.FakeDut'}
        )
        part = Part(part_model, '123456789')

        control_plan = ControlPlan(name='Test for a group of parts',
                                   method_name='',
                                   pars={'sampling': 'every unit'},
                                   from_node=wip,
                                   to_node=des
                                   )

        control = Control(name='Attribute to check on element',
                          method_name='tests.integration.stuff.pas_method',
                          from_node=wip,
                          to_node=des
        )
        control_plan.append_step(control)


        device_generator = Generator(
            name='Generator for inserting devices on wip',
            method_name='tests.integration.stuff.gen_device',
            to_node=wip
        )
        device_generator.add_resource(device_model, 'out')

        insert_device = Flow(device_generator, person)
        insert_device.inputs.append({'tracking': '212121', 'resource_key': 'ms',
                                     'pars': {'class_name': 'tests.integration.stuff.FakeDevice'}})

        try:
            insert_device.prepare()
            insert_device.execute()
        except Exception as e:
            insert_device.cancel()
            raise e
        insert_device.terminate()

        part_generator = Generator(
            name='Generator for parts on wip',
            method_name='tests.integration.stuff.gen_dut_from_label',

            to_node=wip
        )
        part_generator.add_resource(part_model)

        rest = [person, part, device_generator, part_generator,
                insert_device,
                ]
        session.add_all(locations + rest)
        session.commit()
