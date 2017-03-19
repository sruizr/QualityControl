from quactrl import Model, Column, String


class Element(Model):
    __tablename__ = 'elements'
    name = Column(String(50))
    key = Column(String(10))

    def __init__(self, name, key=None):
        self.name = name
        self.key = key

    def __str__(self):
        description = self.name
        if self.key:
                    description += '[{}]'.format(self.key)
        return description

    def __repr__(self):
        identification = '#{} - '.format(self.id)
        return identification + str(self)


class DetectionPoint(Model):
    __tablename__ = 'locations'
    responsible = Column(String)


class Device(Model):
    __tablename__ = 'devices'
    key = Column(String(10))
    name = Column(String(50))
