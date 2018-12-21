from dependency_injector import providers, containers
from quactrl.helpers import get_class


class Data(containers.DynamicContainer):
    """Data layer with all repositories and a session provider
    All is ThreadLocalSingleton
    """
    _MODELS = [
        'hhrr.Person', 'hhrr.Role',
        'operations.Location', 'operations.Part', 'quality.ControlPlan',
        'products.Characteristic', 'products.PartModel', 'products.PartGroup',
        'products.Element', 'products.Attribute', 'products.Characteristic',
        'products.Requirement',
        'quality.Test', 'quality.Mode',
        'devices.DeviceModel', 'devices.Device'
    ]

    def __init__(self, module_name, connection_string=None):
        super().__init__()
        self.connection_string = connection_string
        self.module_name = 'quactrl.data.' + module_name
        SessionClass = get_class('{}.Session'.format(self.module_name))
        self.Session = providers.ThreadLocalSingleton(SessionClass,
                                                      connection_string)
        self._load_repos()

    def _get_class(self, name):
        full_class_name = '{}.{}Repo'.format(self.module_name, name)
        ResultClass = get_class(full_class_name)
        return ResultClass

    def _load_repos(self):
        for model in self._MODELS:
            model_name = model.split('.')[1]
            try:
                RepoClass = self._get_class(model),
            except ImportError:
                RepoClass = self._get_class(model_name)

            Provider = providers.ThreadLocalSingleton(
                RepoClass,
                session=self.Session
            )
            setattr(self, model_name + 's', Provider)
