import datetime


class Event:
    def __init__(self, signal, obj, cavity=1):
        self.signal = signal  # What
        self.obj = obj  # Who
        self.cavity = cavity  # Where
        self.on = datetime.datetime.now()  # When
