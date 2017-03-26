from quactrl import (
    Model, Column, String, ForeignKey, Base, Integer, relationship
)


class ElementComposition(Base):
    __tablename__ = 'element_compositions'

    parent_id = Column(Integer, ForeignKey('elements.id'), primary_key=True)
    parent = relationship("Element", back_populates="composed_by",
                          foreign_keys=[parent_id])

    child_id = Column(Integer, ForeignKey('elements.id'), primary_key=True)
    child = relationship("Element", back_populates="used_by",
                         foreign_keys=[child_id])

    qty = Column(Integer)

    def __init__(self, parent, child, qty=1):
        self.parent = parent
        self.child = child
        self.qty = qty


class Element(Model):
    __tablename__ = 'elements'
    name = Column(String(50))
    key = Column(String(15))
    composed_by = relationship('ElementComposition',back_populates='parent',
                               foreign_keys='ElementComposition.parent_id')
    used_by = relationship('ElementComposition', back_populates='child',
                           foreign_keys='ElementComposition.child_id')

    def __init__(self, name, key=None):
        self.name = name
        self.key = key

    def __str__(self):
        description = self.name
        key_description = '[]'
        if self.key:
            key_description = '[{}]'.format(self.key)

        return self.name + key_description

    def __repr__(self):
        identification = '#{} - '.format(self.id)
        return identification + str(self)


class Operation(Model):
    __tablename__ = 'operations'
    name = Column(String(100))
    responsible = Column(String)


class Device(Model):
    __tablename__ = 'devices'
    key = Column(String(10))
    name = Column(String(50))
