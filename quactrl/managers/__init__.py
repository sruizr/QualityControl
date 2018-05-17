import datetime
from quactrl.domain.persistence import dal


class Event:
    def __init__(self, signal, obj, cavity=1):
        self.signal = signal  # What
        self.obj = obj  # Who
        self.cavity = cavity  # Where
        self.on = datetime.datetime.now()  # When


class Manager:
    """Base class for wrapping dal connection"""
    def __init__(self):
        self.dal = dal

    def connect(self, *args, **kwargs):
        self.dal.connect(*args, **kwargs)
