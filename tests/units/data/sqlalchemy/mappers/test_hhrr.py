from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from quactrl.data.sqlalchemy import metadata
from quactrl.data.sqlalchemy.mappers import core, hhrr
from quactrl.models.hhrr import Role, Person


class A_HhrrModule:
    def setup_class(cls):
        engine = create_engine('sqlite:///:memory:')
        metadata.bind = engine
        engine.echo = True

        metadata.create_all()
        cls.Session = sessionmaker(bind=engine)

    def should_link_roles_and_persons(self):
        session = self.Session()
        person = Person('sruiz', 'salva', 'Ruiz Romero, Salvador')

        role = Role('admin', 'admin', 'Administrator of app')

        person.add_role(role)

        # print(metadata.tables['node_link'].c.from_node_id.name)
        session.add(role)
        session.add(person)
        session.commit()

        assert person in role.persons
        assert len(role.persons) == 1
        assert len(person.roles) == 1

        session = self.Session()
        role = session.query(Role).first()
        assert len(session.query(Role). all()) == 1
        assert role.persons[0].name == 'salva'
