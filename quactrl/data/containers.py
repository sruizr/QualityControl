from dependency_injector import providers, containers
from quactrl.helpers import get_class


class Data(containers.DynamicContainer):

    Session = providers.ThreadLocalSingleton()
    DeviceDefs = providers.ThreadSafeSingleton(
        session=Session)
    Persons = providers.ThreadLocalSingleton(
        session=Session)
    PartModels = providers.ThreadLocalSingleton(
        session=Session)
    Routes = providers.ThreadLocalSingleton(
        session=Session)
    Tests = providers.ThreadLocalSingleton(
        session=Session)
