
from sqlalchemy import create_engine, ForeignKey, Column, UniqueConstraint
from sqlalchemy.orm import sessionmaker, backref, relationship, scoped_session
from quactrl.domain import Base


class DataAccessLayer:
    """Prepare objects for data persistence and return persistence classes of domain"""
    def __init__(self):
        self.connection = None
        self.engine = None
        self.conn_string = None
        self.Session = None
        self._connected = False

    def connect(self, conn_string, **kwargs):

        # connect_args = {}
        # for index in range(1, len(args)):
        #     key, value = args.split('=')
        #     connect_args[key] = value
        echo = kwargs.pop('echo', False)
        self.engine = create_engine(conn_string, connect_args=kwargs['connect_args'],
                                    echo=echo)
        self.metadata = Base.metadata
        try:
            self.connection = self.engine.connect()
            self._connected = True
        except Exception:
            self._connected = False
        DataAccessLayer._connected = True
        self.metadata.create_all(self.engine)

        # Scopped session
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)

    def is_connected(self):
        return DataAccessLayer._connected

    def clear_all_data(self):
        self.metadata.drop_all(self.engine)

    def clear_all_schema(self):
        self.clear_all_data()

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


dal = DataAccessLayer()
