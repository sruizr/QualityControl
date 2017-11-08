from quactrl.samplings import Sampling
from unittest.mock import Mock
# import pytest


class A_Sampling:
    def should_count(self):
        control = Mock()
        sampling = Sampling(control)

        sampling.count()
        control.run.assert_is_called_with()
