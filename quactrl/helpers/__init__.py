import importlib
from ruamel.yaml import YAML


yaml = YAML(typ='safe')


def get_class(full_class_name):
    """Return class by full module path"""
    return _get(full_class_name)


def get_function(full_function_name):
    """Return function by full module path
    """
    return _get(full_function_name)


def _get(component_name):
    packages = component_name.split('.')
    name = packages.pop()
    module = importlib.import_module('.'.join(packages))

    return getattr(module, name)
