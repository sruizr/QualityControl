from sqlalchemy import create_engine, ForeignKey, Column, UniqueConstraint
from sqlalchemy.orm import sessionmaker, backref, relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class DataAccessLayer:

    connection = None
    engine = None
    conn_string = None
    Session = None

    def db_init(self, conn_string, echo=False):
        self.conn_string = conn_string
        self.engine = create_engine(self.conn_string, echo=echo)
        self.metadata = Base.metadata
        self.connection = self.engine.connect()
        self.Session = sessionmaker()

    def prepare_db(self):
        self.metadata.create_all(self.engine)
        self.Session.configure(bind=self.engine)

    def fill_db(self, filler):
        filler.execute()

    def get_batch(key, partnumber):
        """Get or create batch """
        pass

    def get_item(item_data):
        """Get or create item, return None if not possible"""
        pass

    def get_operator(data):
        """Get operator from data layer"""
