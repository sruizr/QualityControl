from quactrl.domain.do import (
    Material, Person, Location, Device
)
from quactrl.domain.base import Resource
from tests.domain.test_data import OnMemoryTest

class A_Material(OnMemoryTest):
    def should_be_created(self):
        resource = Resource('r_key')
        material = Material(resource)

        self.session.add(material)
        self.session.commit()

        assert material.id is not None
        assert material.is_a == 'material'
        assert material.resource == resource


class A_Person(OnMemoryTest):
    def should_be_created(self):
        person = Person('012')

        self.session.add(person)
        self.session.commit()

        assert person.id is not None
        assert person.is_a == 'person'


class A_Location(OnMemoryTest):
    def should_be_created(self):
        location = Location('Qua')

        self.session.add(location)
        self.session.commit()

        assert location.id is not None
        assert location.is_a == 'location'


class A_Device(OnMemoryTest):
    def shoud_be_created(self):
        device = Device()

        self.session.add(device)
        self.session.commit()

        assert device.id is not None
        assert device.is_a == 'device'
