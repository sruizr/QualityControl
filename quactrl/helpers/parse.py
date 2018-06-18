import sys



def from_obj(obj, level=1):
    """Convert object to dictionary, if lazy=True, convert only direct components if they are not primitives"""
    class_name = obj.__class__.__name__.lower()
    method_name = 'from_{}'.format(class_name)
    current_module = sys.modules[__name__]

    try:
        from_method = getattr(current_module, method_name)
    except AttributeError:
        raise Exception('Parsing to dict method is not developed for {}'
                        .format(class_name))

    return from_method(obj, level)

def from_form(form, level=1):
    form_data = from_resource(form)
    return form_data


def from_event(event, level=1):
    event_data = {
        'signal': event.signal,
        'obj': from_obj(event.obj, level-1)}
    if hasattr(event, 'pars'):
        event_data['pars'] = event.pars

    return event_data


def from_test(test, index=None, level=1):
    if test is None:
        test_data = {'status': 'waiting', 'class_name': 'test'}
    else:
        test_data = {
            'class_name': 'test',
            'status': test.status,
            'responsible_key': test.responsible.key,
            'part': from_part(test.part, level-1)
        }

    if index is not None:
        test_data['index'] = index

    return test_data


def from_check(check, index=None, level=1):
    check_data = {
        'class_name': 'check',
        'description': check.path.description.capitalize(),
        'measures': [from_obj(measure) for measure in check.measures],
        'defects': [from_obj(defect) for defect in check.defects],
        'result': check.result,
    }

    if index is not None:
        check_data['index'] = index

    return check_data


def from_part(part, level=1):
    return {
        'class_name': 'part',
        'tracking': part.tracking,
        'key': part.resource.key,
        'name': part.resource.name,
        'description': part.resource.description
    }


def from_measure(measure, level=1):
    data = {'class_name': 'measure',
            'characteristic': from_obj(measure.characteristic),
            'value': measure.qty
            }
    return data


def from_characteristic(char, level=1):
    return {'class_name': 'characteristic',
            'description': char.description.capitalize(),
            'key': char.key
            }


def from_defect(defect, level=1):
    return {'class_name': 'defect',
            'description': defect.description.capitalize(),
            'char_key': defect.characteristic.key
            }

def from_person(person, level=1):
    result = from_node(person)
    roles = [role.key for role in person.roles]
    result['roles'] = roles

    return result

def from_role(role, level=1):
    result = from_node(role)
    result['members'] = [member.key for member in role.members]
    return result


def from_node(node, level=1):
    return {'id': node.id, 'key': node.key, 'description': node.description,
            'name': node.name}


def from_resource(resource, level=1):
    return {'id': resource.id, 'key': resource.key,
            'description': resource.description, 'name': resource.name}


def from_location(location, level=1):
    result = from_node(location)
    result['site'] = location.site.key
    result['parcels'] = [parcel.key for parcel in location.parcels]


def from_path(path, level=1):
    pass
