from threading import Thread, Timer


class Control(Thread):
    def __init__(self):
        pass

    def run():
        # sampling.init(self)
        pass


class Sampling:
    def __init__(self, control):
        self.control = control

    def count(self):
        self.notify_check()  # Default is 100% sampling

    def notify_check(self):
        self.control.run()


class UnitSampling(Sampling):

    def __init__(self, control):
        self.control = control
        self.checked_counter = 0
        self.frequency_counter = 0
        self.order_check = False

    def count(self):
        self.frequency_counter += 1
        if self.frequency_counter >= self.control.sample_frequency:
            self.frequency_counter = 0
            self.checked_counter = 0

        order_check = self.checked_counter < self.control.sample_size
        if order_check:
            self.checked_counter += 1
            self.notify_check()


class TimeSampling(Sampling):
    """ Check /control.sample_frequency/ times every /control.sampling
    _frequency/ seconds"""
    def __init__(self, control):
        super().__init__(control)
        self.checked_counter = 0
        
    def count(self):
        if self.checked_counter == 0:
            self.timer = Timer(self.control.sampling_frequency, self.set_check_order)

            order_check = self.checked_counter < self.control.sample_size
        if order_check:
            self.notify_check()
            self.checked_counter += 1           

    def set_chek_order(self):
        self.checked_counter = 0

class DaySampling(Sampling):
    pass
