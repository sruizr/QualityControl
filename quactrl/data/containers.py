from dependency_injector import providers, containers
import quactrl.data.onmem as onmem
from quactrl.helpers import get_class


class Data(containers.DynamicContainer):
    def __init__(self, args):
        "docstring"

    config = providers.Config()
    Session = providers.ThreadLocalSingleton(config.string_connection)
    Persons = providers.ThreadLocalSingleton(onmem.PersonRepo,
                                             session=Session)
    Roles = providers.ThreadLocalSingleton(onmem.RoleRepo, session=Session)
    Locations = providers.ThreadLocalSingleton(onmem.LocationRepo,
                                               session=Session)
    FailureModes = providers.ThreadLocalSingleton(onmem.FailureModeRepo,
                                                  session=Session)
    Characteristics = providers.ThreadLocalSingleton(onmem.CharacteristicRepo,
                                                     session=Session)
    Elements = providers.ThreadLocalSingleton(onmem.ElementRepo, session=Session)
    Attributes = providers.ThreadLocalSingleton(onmem.AttributeRepo,
                                                session=Session)
    PartModels = providers.ThreadLocalSingleton(onmem.PartModelRepo,
                                                session=Session)
    DeviceModels = providers.ThreadLocalSingleton(onmem.DeviceModelRepo,
                                                  session=Session)
    Devices = providers.ThreadSafeSingleton(onmem.DeviceRepo,
                                            session=Session)

    Parts = providers.ThreadLocalSingleton(onmem.PartRepo, session=Session)
    Routes = providers.ThreadLocalSingleton(onmem.RouteRepo, session=Session)
    Tests = providers.ThreadLocalSingleton(onmem.TestRepo,
                                           session=Session)
