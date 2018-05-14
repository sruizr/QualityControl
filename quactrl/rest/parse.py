import sys
# import quactrl.domain.nodes as nodes
# import quactrl.domain.paths as paths
# import quactrl.domain.resources as resources
# import quactrl.domain.items as items


def from_obj(obj, level=1):
    """Convert object to dictionary, if lazy=True, convert only direct components if they are not primitives"""
    class_name = obj.__class__.__name__.lower()
    method_name = 'from_{}'.format(class_name)
    from_method = getattr(__builtins__, method_name)
    if from_method is None:
        raise Exception('Parsing to dict method is not developed for {}'.format(class_name))

    return from_method(obj, level)


def from_test(test, level):
    pass

def from_check(test, level):
    pass
