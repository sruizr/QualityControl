from tests import TestBase
from unittest.mock import Mock
from quactrl.resources import Element
from quactrl.plan import Characteristic


class A_Characteristic(TestBase):

    def should_give_a_complete_description(self):
        element = Element('elemento', 'key')

        characteristic = Characteristic('atributo', element)

        assert str(characteristic) == 'atributo @ elemento[key]'

    def should_have_requirements(self):
        pass


class A_Control(TestBase):

    def should_have_characteristics(self):
        pass
