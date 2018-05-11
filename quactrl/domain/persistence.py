from sqlalchemy import create_engine, ForeignKey, Column, UniqueConstraint
from sqlalchemy.orm import sessionmaker, backref, relationship, scoped_session
from .base import DataAccessModule as Erp
from .plan import DataAccessModule as Plan
from .do import DataAccessModule as Do
from .check import DataAccessModule as Check
from .act import DataAccessModule as Act
from quactrl.domain import Base


class DataAccessLayer:
    """Prepare objects for data persistence and return persistence classes of domain"""
    def __init__(self):
        self.connection = None
        self.engine = None
        self.conn_string = None
        self.Session = None
        self._connected = False

    def connect(self, connection_string):
        args = connection_string.split(';')
        conn_string = args[0]

        connect_args = {}
        for index in range(1, len(args)):
            key, value = args.split('=')
            connect_args[key] = value
        echo = connect_args.pop('echo', False)
        self.engine = create_engine(conn_string, connect_args=connect_args,
                                    echo=echo)
        self.metadata = Base.metadata
        try:
            self.connection = self.engine.connect()
            self._connected = True
        except Exception:
            self._connected = False

    def is_connected(self):
        return DataAccessLayer._
        DataAccessLayer._connected = True

    # def prepare_db(self):
    #     """Create tables (if no exist) and bind database to class"""
    #     self.metadata.create_all(self.engine)
    #     session_factory = sessionmaker(bind=self.engine)
    #     self.Session = scoped_session(session_factory)

    # def load_dams(self):
    #     self.erp = Erp(self)
    #     self.plan = Plan(self)
    #     self.check = Check(self)
    #     self.do = Do(self)
    #     self.act = Act(self)

    def clear_all_data(self):
        self.metadata.drop_all(self.engine)
        session = self.Session()
        fks = set()
        for table in reversed(self.metadata.sorted_tables):
            for fk in table.foreign_keys:
                fks.add(fk)

        for fk in fks:
            session.execute(fk.drop())

        for table in reversed(self.metadata.sorted_tables):
            session.execute(table.delete())

        session.commit()

    def clear_schema(self):
        pass

    # Generated from managers.Tester
    def get_control_plan_by(self, location, part):
        pass

    def get_responsible_by(self, key):
        pass

    def get_or_create_part(self, part_info, location):
        pass



dal = DataAccessLayer()
