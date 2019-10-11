from dependency_injector import providers, containers
from quactrl.helpers import get_class


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


class Data(containers.DynamicContainer):
    """Data layer with thread local session provider and singleton repositories
    """
    _MODELS = [
        'hhrr.Person', 'hhrr.Role',
        'operations.Location', 'operations.Part', 'quality.ControlPlan',
        'products.Characteristic', 'products.PartModel', 'products.PartGroup',
        'products.Element', 'products.Attribute', 'products.Characteristic',
        'products.Requirement',
        'quality.Test', 'quality.Mode',
        'devices.DeviceModel', 'devices.Device',
        'documents.Directory', 'documents.Form',
        'quality.Measurement'
    ]

    def __init__(self, module_name, connection_string=None,
                 custom_repo_path=None, **kwargs):
        super().__init__()
        self.connection_string = connection_string
        self.module_name = 'quactrl.data.' + module_name

        self.db = get_class('{}.Db'.format(self.module_name))(
            connection_string, **kwargs
        )

        self.Session = providers.ThreadLocalSingleton(self.db.Session)

        self._repo_path = custom_repo_path
        self._load_repos()

    def drop_all(self):
        """Remove all tables and schemas, including data!
        """
        self.db.drop_all()

    def create_schema(self):
        """Create schema on database with empty tables
        """

        self.db.create_schema()

    def _find_repo_class(self, model):
        module_name = self._repo_path if self._repo_path else self.module_name

        # repo_path.model_path
        RepoClass = self._get_repo_class(module_name, model)

        if not RepoClass:  # module_path.model_path
            RepoClass = self._get_repo_class(self.module_name, model)

        model = model.split('.')[1]
        if not RepoClass:  # repo_path.model_name
            RepoClass = self._get_repo_class(module_name, model)

        if not RepoClass:  # module_path.model_name
            RepoClass = self._get_repo_class(self.module_name, model)

        return RepoClass

    def _get_repo_class(self, module_name, model_name):
        repo_path = '{}.{}Repo'.format(module_name, model_name)

        try:
            RepoClass = get_class(repo_path)
        except ImportError:  # Not found class
            return

        return RepoClass

    def _load_repos(self):
        for model in self._MODELS:
            RepoClass = self._find_repo_class(model)
            if RepoClass:
                Provider = providers.ThreadSafeSingleton(
                    RepoClass,
                    data=self)
                model_name = model.split('.')[-1]
                setattr(self, model_name + 's', Provider)


class Repository:
    def __init__(self, data):
        """Base class for a repositry class with session pattern
        """
        self.data = data

    @property
    def session(self):
        return self.data.Session()

    def add(self, obj):
        self.session.add(obj)

    def remove(self, obj):
        self.session.delete(obj)
