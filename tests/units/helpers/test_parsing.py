from unittest.mock import Mock
import quactrl.helpers.parsing as parsing
import pytest
import quactrl.domain.resources as r
import quactrl.domain.nodes as n
import quactrl.domain.items as i
import quactrl.domain.paths as p


def test_parse_part():
    part = Mock()+
    part.tracking = '123456789'
    part.part_model.name = 'part_name'
    part.resource.key = 'part_number'
    part.resource.description = 'part description'
    result = parsing.parse(part)
    expected = {
        'type': 'part',
        'tracking': '123456789',
        'part_model': {
            'name': 'part_name',
            'key': 'part_number',
            'description': 'part description'
            }
    }
    assert result == expected


def test_parse_test():
    parse.from_part = lambda x, y: {'key': 'part'}
    test = Mock()
    part = Mock()
    part.__class__.__name__ = 'part'
    test.path.description = 'Control plan description'
    test.path.id = 1234
    test.status = 'iddle'
    test.responsible.key = 'sruiz'

    result = parse.from_test(test)

    expected = {
        'status': 'iddle',
        'class_name': 'test',
        'part': {'key': 'part'},
        'responsible_key': 'sruiz'
    }
    assert result == expected

    result = parse.from_test(None)
    assert result == {'status': 'waiting',
                      'class_name': 'test'}


def test_parse_event():
    parse.from_mock = lambda m, y: {'key': m.key}
    obj = Mock(key='obj')
    event = Mock()
    event.signal = 'signal'
    event.obj = obj
    del event.pars

    event_data = parse.from_event(event)
    expected = {
        'signal': 'signal',
        'obj': {'key': 'obj'},
    }

    assert event_data == expected

    event.pars = {'foo': 'foo'}
    event_data = parse.from_event(event)
    expected['pars'] = {'foo': 'foo'}

    assert event_data == expected


def test_parse_check():
    check = Mock()
    check.path.description = 'check description'
    check.measures = [Mock(key='measure_{}'.format(_i))
                      for _i in range(1)]
    check.defects = [Mock(key='defect_{}'.format(_i))
                          for _i in range(2)]
    check.result = 'nok'

    check_data = parse.from_check(check, '1.1')

    expected = {
        'class_name': 'check',
        'index': '1.1',
        'description': 'Check description',
        'defects': [{'key': 'defect_0'}, {'key': 'defect_1'}],
        'measures': [{'key': 'measure_0'}],
        'result': 'nok'
    }
    assert check_data == expected


def test_parse_measure():
    measure = Mock()
    measure.characteristic.key = 'char'
    measure.qty = 1.2
    measure_data = parse.from_measure(measure)

    expected = {
        'class_name': 'measure',
        'characteristic': {'key': 'char'},
        'value': 1.2
    }
    assert measure_data == expected


def test_parse_characteristic():
    characteristic = Mock()
    characteristic.description = 'char description'
    characteristic.key = 'char_key'
    char_data = parsing.parse(characteristic)

    expected = {'class_name': 'characteristic',
                'description': 'Char description',
                'key': 'char_key'
    }
    assert char_data == expected


def test_parse_defect():
    defect = Mock()
    defect.description = 'defect description'
    defect.characteristic.key = 'char'
    defect_data = parsing.parse(defect)
    expected = {
        'class_name': 'defect',
        'description': 'Defect description',
        'char_key': 'char'
    }
