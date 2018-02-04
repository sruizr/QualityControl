from quactrl.domain.do import Person, Device, Group, Location, Part
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
                                   'Measure system to be used by the check')
        device = Device(
            device_model, '00000',
            pars={'class_name': 'tests.integration.stuff.FakeDevice'}
        )

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

        # generator = Generator
        rest = [person, device]
        session.add_all(locations + rest)
        session.commit()



        # model_157695 = PartModel('311574695',
        #                          'CAMRegis.H VL5 Registrador de Temperatura')

        # operation = Operation(
        #     method_name='final_test',
        #     from_node=wip_t,
        #     to_node=despatch
        #     )
        # operation.add_resource(model_157695)

        # control_plan = ControlPlan(
        #     method_name='product_test'
        #     )
        # control_plan.add_resource(model_157695)
        # operation.add_step(control_plan)

        # characteristics = {
        #     'T_env': Characteristic('T_env', 'temperatura en ambiente'),
        #     'P_env': Characteristic('P_env', 'presión en ambiente'),
        #     'C_bth': Characteristic('C_bth', 'condiciones en baño'),
        #     'St_bth': Characteristic('StT_bth',
        #                              'estabilidad temperatura en baño'),
        #     'tSt_bth': Characteristic('tSt_bth',
        #                               'tiempo estabilización en baño'),
        #     'U_bth': Characteristic('UT_bth', 'uniformidad de temperatura en baño'),
        #     'dT_p': Characteristic('dT_p', 'desviación temperatura en patrón'),
        #     'T_p': Characteristic('T_p', 'temperatura en patrón'),
        #     'T_d': Characteristic('T_d', 'temperatura en termómetro'),
        #     'eT_d': Characteristic('eT_d', 'error de temperatura en termómetro')
        #     }

        # environment_control = Control(
        #     method_name='en12830.eval_environment'
        # )
        # environment_control.add_characteristic(characteristics['T_env'],
        #                                        limits=[20, 26])
        # environment_control.add_characteristic(characteristics['P_env'],
        #                                        limits=[0.4, 0.8])
        # environment_control.add_characteristic(characteristics['P_env'])
        # control_plan.add_step(environment_control)

        # bath_control = Control(
        #     method_name='en12830.eval_bath_conditions',
        #     pars={
        #         'bath_number': 0,
        #         'setup_temperature': 30,
        #         'time_to_stable': 30,
        #         'step': 'A'
        #         }
        #     )
        # bath_control.add_characteristic(characteristics['tSt_bth'],
        #                                 limits=[120, 300])
        # bath_control.add_characteristic(characteristics['St_bth'],
        #                                 limits=[-0.1, 0.1])
        # bath_control.add_characteristic(characteristics['U_bth'],
        #                                 limits=[-0.05, 0.05])
        # # control_plan.add_step(bath_control)

        # temperature_control = Control(
        #     method_name='en12830.eval_temperature_errors',
        #     pars={
        #         'bath_number': 0,
        #         'uncertainty': 0.11,
        #         'uniformity_correction': 0.1,
        #         'step': 'A'
        #         }
        #     )
        # temperature_control.add_characteristic(characteristics['T_p'],
        #                                        qty=2.0)
        # temperature_control.add_characteristic(characteristics['eT_d'],
        #                                        qty=5.0, limits=[-1, 1])
        # temperature_control.add_characteristic(characteristics['T_d'],
        #                                        qty=5.0)
        # # control_plan.add_step(temperature_control)


        # all = persons + devices + list(characteristics.values()) + [operation]
        # session.add_all(all
        # )
        # session.commit()
