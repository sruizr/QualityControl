from sqlalchemy import create_engine
from quactrl.data.sqlalchemy.tables import metadata


class A_TableModule:
    def setup_class(cls):
        cls.db = create_engine('sqlite:///test.db')
        cls.db.echo = True

    def should_create_tables(self):
        metadata.bind = self.db
        metadata.create_all()
