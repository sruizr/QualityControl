import threading
from quactrl.managers import Feedback
import pytest


class FeedbackCaller(threading.Thread):
    def __init__(self, message, answer_template):
        super().__init__()
        self.feedback = Feedback(message, answer_template)

    def run(self):
        self.feedback.wait()


@pytest.mark.current
class A_Feedback:
    def should_waits_till_receive_feedback_from_client(self):
        caller = FeedbackCaller({'key': 'message'}, ['data'])
        caller.start()

        assert caller.is_alive()
        caller.feedback.answer({'data': 1})

        caller.join(timeout=0.5)
        assert not caller.is_alive()
        assert caller.feedback.data == {'data': 1}

    def should_raise_exception_if_data_not_supplied(self):
        caller = FeedbackCaller({'key': 'messge'}, ['data'])
        caller.start()
        try:
            caller.answer({})
            pytest.fails('Not exception is raised')
            caller.join(timeout=0.5)
            assert not caller.is_alive()
        except Exception as e:
            caller.feedback.set()
