from sqlalchemy import create_engine, ForeignKey, Column, UniqueConstraint
from sqlalchemy.orm import sessionmaker, backref, relationship
from .erp import DataAccessModule as Erp
from .plan import DataAccessModule as Plan
from .do import DataAccessModule as Do
from .check import DataAccessModule as Check
from .act import DataAccessModule as Act
from quactrl.domain import Base


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

    def __init__(self, file_path=None):
        self.file_path = file_path
        self.erp = Erp(self)
        self.plan = Plan(self)
        self.check = Check(self)
        self.do = Do(self)
        self.act = Act(self)

    def db_init(self, connection_string):
        args = connection_string.split(';')
        self.connection_string = args[0]

        self.option_args = {}
        if len(args) > 1:
            option_args = {}

            self.conn_string = conn_string
            self.engine = create_engine(self.conn_string, echo=echo)
            self.engine = create_engine(self.conn_string, # echo=echo)
                                        connect_args={'check_same_thread': False},
                                        echo=echo)
            self.metadata = Base.metadata
            self.connection = self.engine.connect()
            self.Session = sessionmaker()

    def prepare_db(self):
        """Create tables (if no exist) and bind database to class"""
        self.metadata.create_all(self.engine)
        self.Session.configure(bind=self.engine)

    def load_db(self, filler):
        filler.load()

    def clear_all_data(self):
        self.metadata.drop_all(self.engine)
        # session = self.Session()
        # fks = set()
        # for table in reversed(self.metadata.sorted_tables):
        #     for fk in table.foreign_keys:
        #         fks.add(fk)

        # for fk in fks:
        #     session.execute(fk.drop())

        # for table in reversed(self.metadata.sorted_tables):
        #     session.execute(table.delete())

        # session.commit()

    def clear_schema(self):
        pass
