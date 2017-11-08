from tests import TestBase
from unittest.mock import Mock
from quactrl.resources import (
    Element, Operation
)
from quactrl.plan import (
    Characteristic, Sampling, Reaction, Method, FailureMode, Control
)


class A_Characteristic(TestBase):

    def should_give_a_complete_description(self):
        element = Element('elemento', 'key')

        characteristic = Characteristic('atributo', element)

        assert str(characteristic) == 'atributo @ elemento[key]'

    def should_have_requirements(self):
        pass


class A_Control(TestBase):
    def should_have_characteristics(self):
        element = Element('elemento, key')
        characteristic = Characteristic('atributo', element)

        method = Method('método')
        detection_point = Operation('operacion', 'role')
        control = Control(characteristic, Sampling.by_day, method,
                          detection_point)
