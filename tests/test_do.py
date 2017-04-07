from tests import TestBase
from unittest.mock import Mock
from quactrl.resources import (
    Element, Operation
)
from quactrl.plan import (
    Characteristic, Sampling, Reaction, Method, FailureMode, Control
)

from quactrl.do import (
    Batch, Item, Check
)


class A_Check(TestBase):

    def should_init_with
