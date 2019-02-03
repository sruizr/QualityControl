def load_all_mappers():
    mappers = ['core' ,'hhrr', 'products', 'operations', 'quality', 'devices']
    # Without this order the loading cracks...
    for mapper in mappers:
        _ = __import__('quactrl.data.sqlalchemy.mappers.{}'.format(mapper))
