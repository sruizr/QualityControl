from threading import Thread, Event


class StoppableThread(Thread):
    """Template for a thread which can receive a stop signal"""
    def __init__(self):
        super().__init__()
        self.stop_event = Event()

    def run(self):
        while not self.stop_event.is_set():
            self.loop()

    def stop(self):
        self.stop_event.set()
        self.join()

    def loop(self):
        pass
