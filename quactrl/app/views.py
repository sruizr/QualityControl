from abc import ABC, abstractmethod


class InspectionView(ABC):
    """View layer of Inspection app, it must be inherited"""
    def __init__(self, environment):
        self.env = environment
        self.controller = self.env.controller
        self.env.view = self

    @abstractmethod
    def read_operator(self):
        """Sync call to return the operator information from user interface"""
        pass

    @abstractmethod
    def read_batch(self, cavity=0):
        """Sync call to return batch information from user interface"""
        pass

    @abstractmethod
    def read_item(self, cavity=0):
        """Sync call to return the item information from user interface"""
        pass

    @abstractmethod
    def update_check(self, value):
        """Called by inspection service when a check has changed"""
        pass

    @abstractmethod
    def update_test(self, value):
        """Called by inspection service when test has changed"""
        pass

    @abstractmethod
    def show_error(self, message_key, **kwargs):
        """Called by controller when an error has happened"""
        return None

    @abstractmethod
    def user_confirmation(self, key, **kwargs):
        """Sync call by inspection confirmation to get confirmation by user
        returns False if confirmation is cancelled
        """
        pass
