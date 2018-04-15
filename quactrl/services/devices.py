from queue import Queue
import types
from threading import Thread, Lock
from quactrl.helpers import get_class

class DeviceManager:
    pass


class DeviceProxy:
    def __init__(self, implementation):
        self._impl = implementation

    def __getattr__(self, name):
        pass


    def _has_method(self, name):
        return self


class Worker:
    def __init__(self, request_queue):
        self._in = request_queue
        self.stop = False

    def run(self):
        while not self.stop:
            order = self._in.get()
            client = order[0]
