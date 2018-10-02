from quactrl.helpers import get_class

class FakeClass:
    pass


def test_get_class():
    assert get_class('tests.unit.helpers.test_init.FakeClass') == FakeClass
