from sqlalchemy.orm import synonym, reconstructor, aliased
from quactrl.domain.base import Item, ItemRelation
from quactrl.domain import get_component



class Material(Item):
    __mapper_args__ = {'polymorphic_identity': 'material'}


class Part(Item):
    __mapper_args__ = {'polymorphic_identity': 'part'}

    def __init__(self, part_model, **kwargs):

        Item.__init__(self, resource=part_model, **kwargs)
        self._bh = None

    @reconstructor
    def after_load(self):
        self._bh = None

    @property
    def bh(self):
        """Loads bh just when requested"""
        if self._bh is None:
            self._bh = self.resource.get_behaviour()
        return self._bh


class Device(Item):
    __mapper_args__ = {'polymorphic_identity': 'device'}

    def __init__(self, device_model, tracking, **kwargs):
        Item.__init__(self,
                      resource=device_model, tracking=tracking, **kwargs)
        self.bh = None

    def setup(self):
        if not self.resource.pars:
            return None # No class to load

        resource_pars = self.resource.pars.get()
        if 'class_name' not in resource_pars:
            return None # No class to load

        class_name = resource_pars['class_name']
        FunctionalDevice = get_component(class_name)

        if not FunctionalDevice:
            raise Exception('class path {} can not be loaded'.format(class_name))

        pars = {}
        if self.pars:
            pars = self.pars.get()
            self.bh = FunctionalDevice(**pars)
        else:
            self.bh = FunctionalDevice()

    def assembly(self, devices):
        if self.bh:
            self.bh.assembly(devices)

    @reconstructor
    def after_load(self):
        self.bh = None


class Report(Item):
    pass


class Defect(Item):
    __mapper_args__ = {'polymorphic_identity': 'defect'}
    failure_mode = synonym('resource')


class Measurement(Item):
    __mapper_args__ = {'polymorphic_identity': 'measurement'}
    characteristic = synonym('resource')
