from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from quactrl.data.sqlalchemy import metadata


class TestMapper:
    def setup_class(cls):
        engine = create_engine('sqlite:///:memory:')
        metadata.bind = engine

        metadata.create_all()
        cls.Session = sessionmaker(bind=engine)

    #
