from sqlalchemy import create_engine, ForeignKey, Column, UniqueConstraint
from sqlalchemy.orm import sessionmaker, backref, relationship
from sqlalchemy.ext.declarative import declarative_base

from .erp import DataAccessModule as Erp
from .plan import DataAccessModule as Plan
from .do import DateAccessModule as Do
from .check import DataAccessModule as Check
from .act import DataAccessModule as Act


Base = declarative_base()


class DataAccessLayer:
    """Prepare objects for data persistence and return persistence classes of domain"""

    connection = None
    engine = None
    conn_string = None
    Session = None
    erp = None
    plan = None
    do = None
    check = None
    act = None

    def __init__(self, file_path):
        self.file_path = file_path
        self.erp = Erp(self)
        self.plan = Plan(self)
        self.check = Check(self)
        self.do = Do(self)
        self.act = Act(self)

    def db_init(self, conn_string, echo=False):
        self.conn_string = conn_string
        self.engine = create_engine(self.conn_string, echo=echo)
        self.metadata = Base.metadata
        self.connection = self.engine.connect()
        self.Session = sessionmaker()

    def prepare_db(self):
        """Create tables (if no exist) and bind database to class"""
        self.metadata.create_all(self.engine)
        self.Session.configure(bind=self.engine)
