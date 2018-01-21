from quactrl import get_class


class Environment:
    def __init__(self, config, fill_db=False):
        """Generate all layers for application from config dict"""
        self.pars = config.get('parameters', {})

        DataAccessLayer = get_class(config['DataAccessLayer'])
        self.dal = DataAccessLayer()
        self.dal.conn_string = config['data_conn_string']
        self.dal.db_init()
        self.dal.prepare_db()
        if fill_db:
            DataFiller = get_class(config['data_filler'])
            self.domain.fill_db(DataFiller())

        Service = get_class(config['service'])
        self.service = Service(self)
        self.service.set_process(config['process'])

        Controller = get_class(config['controller'])
        self.controller = Controller(self)

        View = get_class(config['view'])
        self.view = View(self)

    def run(self):
        self.controller.start()
        self.view.run()
