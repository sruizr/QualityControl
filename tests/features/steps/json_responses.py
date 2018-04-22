import trafaret as t
from trafaret.constructor import construct


Item = construct(
    {'resource_key': str, 'resource_description': str,
                  ''
TestData = construct({})
CheckData = construct({})


EventData = construct({'object': (TestData | CheckData),
                   'event_name': str|})
EventData.allow_extra('cavity')

EventsData = construct([Event])
