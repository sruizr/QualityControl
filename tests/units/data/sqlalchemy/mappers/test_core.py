from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from quactrl.data.sqlalchemy import metadata
from quactrl.data.sqlalchemy import tables
from quactrl.data.sqlalchemy.mappers import core



class A_CoreModule:
    def setup_class(cls):
        engine = create_engine('sqlite:////memory')
        metadata.bind = engine

        metadata.create_all()
