def load_all_mappers():
    mappers = ['core'] #  ,'hhrr', 'operations', 'products', 'quality']

    for mapper in mappers:
        _ = __import__('quactrl.data.sqlalchemy.mappers.{}'.format(mapper))
