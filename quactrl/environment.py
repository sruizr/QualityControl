from quactrl.entities import DataAccessLayer



class Environment:
    def __init__(self, dal, service, controller, view):
        self.dal = dal
        self.service = service
        self.controller = controller
        self.view
