from quactrl.domain.do import (
    Material, Person, Location, Device
)
from quactrl.domain.erp import Resource
from tests.domain.test_data import OnMemoryTest


class A_Material(OnMemoryTest):
    def should_be_created(self):
        resource = Resource()
        material = Material(resource)

        session = self.dal.Session()
        session.add(material)
        session.commit()

        assert material.id is not None
        assert material.is_a == 'material'
        assert material.resource == resource


class A_Person(OnMemoryTest):
    def should_be_created(self):
        person = Person('012')

        session = self.dal.Session()
        session.add(person)
        session.commit()

        assert person.id is not None
        assert person.is_a == 'person'


class A_Location(OnMemoryTest):
    def should_be_created(self):
        location = Location('Qua')

        session = self.dal.Session()
        session.add(location)
        session.commit()

        assert location.id is not None
        assert location.is_a == 'location'


class A_Device(OnMemoryTest):
    def shoud_be_created(self):
        device = Device()

        session = self.dal.Session()
        session.add(device)
        session.commit()

        assert device.id is not None
        assert device.is_a == 'device'
