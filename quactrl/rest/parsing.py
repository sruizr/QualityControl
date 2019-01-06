def parse(obj):
    if obj is None:
        return None

    result = {}

    name = obj.__class__.__name__
    if name in _PARSES:
        return _PARSES[name](obj)
    elif issubclass(type(obj), Exception):
        return _parse_error(obj)
    else:
        raise Exception('"{}" parsing is not modelled'.format(name))


def _parse_id(obj, obj_dict):
    if hasattr(obj, '_id'):
        obj_dict['_id'] = obj._id


def _parse_person(person):
    result = {
        'class': 'Person',
        'key': person.key,
        'name': person.name,
        'full_name': person.description}
    _parse_id(person, result)
    return result


def _parse_test(test):
    result = {
        'class': 'Test',
        'started_on': test.started_on.isoformat(),
        'part': parse(test.part),
        'finished_on': test.finished_on.isoformat() if test.finished_on else None
    }
    _parse_id(test, result)
    return result


def _parse_cavity(cavity):
    result = {
        'state': cavity.state,
        'part': parse(cavity.part)
    }
    return result


def _parse_check(check):
    result = {
        'class': 'Check',
        'description': check.description,
        'result': check.state,
        'measurements': [],
        'defects': [],
        'started_on': check.started_on.isoformat(),
        'finished_on': check.finished_on.isoformat() if check.finished_on else None
    }
    _parse_id(check, result)

    for measurement in check.measurements:
        result['measurements'].append(parse(measurement))

    for defect in check.defects:
        result['defects'].append(parse(defect))

    return result


def _parse_measurement(measurement):
    result = {
        'characteristic': '{}>{}'.format(measurement.characteristic.key,
                                         measurement.tracking),
        'value': measurement.value
    }
    _parse_id(measurement, result)
    return result


def _parse_defect(defect):
    result = {
        'failure_description': defect.failure_mode.description,
        'tracking': defect.tracking
    }
    _parse_id(defect, result)
    return result


def _parse_action(action):
    result = {
        'class': 'Action',
        'description': action.description,
        'result': action.state,
        'started_on': action.started_on.isoformat(),
        'finished_on': action.finished_on.isoformat() if action.finished_on
        else None
    }
    _parse_id(action, result)
    return result


def _parse_location(location):
    result = {
        'class': 'Location',
        'key': location.key,
        'name': location.name,
        'description': location.description
    }
    _parse_id(location, result)
    return result


def _parse_part(part):
    result = {
        'class': 'Part',
        'part_number': part.model.key,
        'part_description': part.model.description,
        'serial_number': part.serial_number}
    if part.pars:
        result.update(part.pars)

    return result


def _parse_part_model(model):
    result = {
        'class': 'PartModel',
        'part_number': model.key,
        'part_name': model.name,
        'part_description': model.description
    }
    _parse_id(model, result)
    return result


def _parse_error(error):
    result = {
        'class': 'Error',
        'name': error.__class__.__name__,
        'message': str(error)
    }
    return result


_PARSES = {
    'Test': _parse_test,
    'Check': _parse_check,
    'Person': _parse_person,
    'Action': _parse_action,
    'Measurement': _parse_measurement,
    'Defect': _parse_defect,
    'PartModel': _parse_part_model,
    'Cavity': _parse_cavity,
    'Part': _parse_part
}
