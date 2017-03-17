from quactrl import Model


class Element(Model):
    __tablename__ = 'elements'


class DetectionPoint(Model):
    __tablename__ = 'operations'
    responsible = Column(String)
