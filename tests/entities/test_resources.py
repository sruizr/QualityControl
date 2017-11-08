from tests import TestBase
from unittest.mock import Mock
from quactrl.resources import Element, ElementComposition


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

        composition_1 = ElementComposition(parent, child_1)
        composition_2 = ElementComposition(parent, child_2, qty=2)

        assert len(parent.used_by) == 0
        assert len(parent.composed_by) == 2
        assert child_1.used_by[0].parent == parent
        assert child_2.used_by[0].parent == parent

