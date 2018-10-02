# import datetime
# import threading
# from quactrl.domain.persistence import dal


# class Event:
#     def __init__(self, signal, obj):
#         self.signal = signal  # What
#         self.obj = obj  # Who
#         self.on = datetime.datetime.now()  # When


# class Feedback(threading.Event):
#     """Manages feedback from user and waits until is answered"""
#     def __init__(self, message, answer_fields=None):
#         super().__init__()
#         self.message = message
#         if answer_fields is None:
#             answer_fields = []
#         self.answer_fields = answer_fields
#         self.data = None

#     def answer(self, data):
#         for field in self.answer_fields:
#             if field not in data:
#                 self.set()
#                 raise Exception('Lack of {} information'.format(field))

#         self.data = data
#         self.set()


# class Manager:
#     """Base class for wrapping dal connection"""
#     def __init__(self):
#         self.dal = dal

#     def connect(self, kwargs):
#         connection_string = kwargs.pop('connection_string')
#         self.dal.connect(connection_string, **kwargs)
#         return True
