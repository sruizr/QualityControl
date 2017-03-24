from tests import TestBase
from unittest.mock import Mock
from quactrl.resources import Element


class A_Element(TestBase):

    def should_give_a_complete_description(self):
        element_with_key = Element('pantalla')
        assert str(element_with_key) == 'pantalla[]'

        element = Element('pantalla', 'aaa')
        assert str(element) == 'pantalla[aaa]'

    def should_be_composed_by_other_elements(self):
        parent = Element('pantalla')
        child_1 = Element('led 1')
        child_2 = Element('led 2')

        # parent.composed_by.append(child_1)
        # parent.composed_by.append(child_2)

    #     assert parent in child_1.used_by
    #     assert parent in child_2.used_by
