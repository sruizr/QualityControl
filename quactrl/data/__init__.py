from dependency_injector import providers, containers
from quactrl.helpers import get_class
import inspect
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class NotFoundPart(Exception):
    pass


class NotFoundPath(Exception):
    pass


class NotFoundItem(Exception):
    pass


class NotFoundResource(Exception):
    pass


class NotFoundNode(Exception):
    pass


class DataAccessLayer(containers.DynamicContainer):
    """Data Access layer with thread local singleton session and repositories
    """

    def __init__(self, module_name, connection_string=None, **kwargs):
        super().__init__()
        self.db = get_class('quactrl.data.{}.Database'.format(module_name))(
            connection_string, **kwargs
        )
        self.Session = providers.ThreadLocalSingleton(self.db.Session)
        self._load_repositories('quactrl.data.' + module_name)
        # self._load_absent_repositories()

    def drop_all(self):
        """Remove all tables and schemas, including dal!
        """
        self.db.drop_all()

    def create_schema(self):
        """Create schema on dalbase with empty tables
        """
        self.db.create_schema()

    def _load_repositories(self, module_name):
        base_module = module_name.split('.')[-1]
        module = __import__(module_name).data
        module = getattr(module, base_module)
        for name, obj in inspect.getmembers(module):
            # if inspect.ismodule(obj):

            #     self._load_repos('{}.{}'.format(module_e, name))
            if inspect.isclass(obj) and name[-4:] == 'Repo':
                Provider = providers.ThreadSafeSingleton(obj, self)
                setattr(self, name[:-4] + 's', Provider)
                logger.debug('Loaded repository {}'.format(name[:-4]))

    # def _load_absent_repositories(self):
    #     module = __import__('quactrl.data.repositories').data.repositories
    #     for name, obj in inspect.getmembers(module):
    #         if inspect.isclass(obj) and name[-4:] == 'Repo':
    #             if not hasattr(self, name[:-4] + 's'):
    #                 Provider = providers.ThreadSafeSingleton(obj, self)
    #                 setattr(self, name[:-4] + 's', Provider)
    #                 logger.debug('Loaded default repository {}'.format(name[:-4]))

    def commit(self):
        self.Session().commit()

    def rollback(self):
        self.Session().rollback()
