from sqlalchemy import (Column, Integer, Numeric, String,
                        DateTime, ForeignKey, Boolean, create_engine)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DataAccessLayer:
    connection = None
    engine = None
    conn_string = None

    def db_init(self, conn_string, echo=False):
        self.engine = create_engine(conn_string or self.conn_string, echo=echo)
        self.metadata.create_all(self.engine)
        self.connection = self.engine.connect()

dal = DataAccessLayer()
