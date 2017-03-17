from quactrl import Model, Column, String, Integer


class Element(Model):
    __tablename__ = 'elements'
    name = Column(String(30))
    key = Column(String(10))


class DetectionPoint(Model):
    __tablename__ = 'operations'
    responsible = Column(String)
