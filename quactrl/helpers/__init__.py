import importlib


def get_class(full_class_name):
    """Return class by ful module path"""
    packages = full_class_name.split('.')
    class_name = packages.pop()
    module = importlib.import_module('.'.join(packages))

    return getattr(module, class_name)
#
