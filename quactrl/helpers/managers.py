from threading import Thread, Event


class StoppableThread(Thread):

    def __init__(self):
        super().__init__()
        self.stop_event = Event()

    def run(self):
        while not self.stop_event.is_set():
            self.loop()

    def stop(self):
        self.stop_event.set()

    def loop(self):
        pass
