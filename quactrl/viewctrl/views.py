from abc import ABC, abstractmethod


class InspectionView(ABC):
    """View layer of Inspection Application, it must be inherited"""
    def __init__(self, environment):
        self.controller = environment.controller

    def run(self):
        self.show_welcome()
        self.get_operator_key()

    def get_operator_key(self):
        """ First step """
        operator_key = self.read_operator()
        self.controller.open_session(self, operator_key)

    @abstractmethod
    def read_operator(self):
        """Return the operator key"""
        pass

    def get_batch_data(self):
        batch_data = self.read_batch()
        self.controller.start_batch(batch_data)

    @abstractmethod
    def read_batch(self, cavity=0):
        """Return 'key' and 'partnumber' values of batch"""
        pass

    @abstractmethod
    def read_item(self, cavity=0):
        pass

    @abstractmethod
    def show_welcome(self):
        pass

    def update_check(self, check):
        if check.progress == 0:
            self.show_check_initialized(check)
        elif check.progress == 100:
            self.show_check_result(check)
        else:
            self.show_check_progress(check)

    @abstractmethod
    def show_check_result(self, check):
        pass

    @abstractmethod
    def show_check_initialized(self, check):
        pass

    def show_check_progress(self, check):
        pass

    def update_test(self, test):
        if test.status != 'pending':
            self.controller.end_test(test)

    @abstractmethod
    def show_resume(self, test):
        pass

    @abstractmethod
    def show_test_started(self, test):
        pass

    @abstractmethod
    def show_error(self, message):
        pass

    def get_operator_confirmation(self, message):
        pass
