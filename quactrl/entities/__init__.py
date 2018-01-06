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
        self.engine = create_engine(conn_string or self.conn_string, echo=echo)
        self.metadata = Base.metadata
        self.connection = self.engine.connect()
        self.Session = sessionmaker()

    def prepare_db(self):
        self.metadata.create_all(self.engine)
        self.Session.configure(bind=self.engine)
