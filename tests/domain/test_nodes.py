import quactrl.domain.nodes as n
from tests.domain import EmptyDataTest


class A_Person(EmptyDataTest):
    def should_have_roles(self):

        role_1 = n.Role()
        role_2 = n.Role()

        person = n.Person()

        person.roles.append(role_1)
        person.roles.append(role_2)

        self.session.add(person)
        self.session.commit()

        assert len(person.roles) == 2
        assert role_1.persons[0] == person


class A_Role(EmptyDataTest):
    def should_have_members(self):
        person_1 = n.Person()
        person_2 = n.Person()

        role = n.Role()

        role.persons.extend([person_1, person_2])

        self.session.add(role)
        self.session.commit()

        assert person_1.roles[0] == role


class A_Location(EmptyDataTest):
    def should_have_parcels(self):
        locations = [n.Location() for _ in range(3)]

        location = locations[2]
        location.parcels.extend(locations[1:])

        self.session.add(location)
        self.session.commit()

        assert len(location.parcels) == 2
        assert location.parcels[0].site == location

    def should_have_one_site(self):
        locations = [n.Location() for _ in range(3)]

        site = locations[0]
        locations[1].site = site
        locations[2].site = site

        self.session.add(site)
        self.session.commit()

        assert len(site.parcels) == 2

        locations[1].site = locations[2]
        self.session.flush()

        assert len(site.parcels) == 1

    def should_have_owners(self):
        owner = n.Role()
        location = n.Location()

        location.owners.append(owner)

        self.session.add(location)
        self.session.commit()

        assert location.owners[0] == owner
        assert len(location.parcels) == 0

        parcel = n.Location()
        location.parcels.append(parcel)
        self.session.flush()

        assert len(location.owners) == 1
        assert parcel.site == location
