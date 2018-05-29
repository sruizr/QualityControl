from sqlalchemy.orm import relationship, synonym, reconstructor, aliased
from sqlalchemy.ext.hybrid import hybrid_property
from quactrl.domain.base import Item, ItemLink
from quactrl.domain import get_component


class Part(Item):
    __mapper_args__ = {'polymorphic_identity': 'part'}
    defects = relationship(
        'Defect', secondary=ItemLink,
        primaryjoin=Item.id == ItemLink.c.from_item_id,
        secondaryjoin=Item.id == ItemLink.c.to_item_id,
        backref='_parts')
    measurements = relationship(
        'Measurement', secondary=ItemLink,
        primaryjoin=Item.id == ItemLink.c.from_item_id,
        secondaryjoin=Item.id == ItemLink.c.to_item_id,
        backref='_parts')

    def __init__(self, part_model, **kwargs):
        Item.__init__(self, resource=part_model, **kwargs)
        self._bh = None
        self._decorator = None

    def decorate(self):
        self._decorator = None  # TODO

    def __getattr__(self, key):
        try:
            return super().__getattr__(key)
        except AttributeError:

            raise AttributeError()

    def add_defect(self, failure_mode, element_key=None):
        """Add a defect from failure_mode and returns it"""
        tracking = self.tracking + '/' + failure_mode.key
        tracking = tracking + '_' + element_key if element_key else tracking
        for defect in self.defects:
            if defect.failure_mode and defect.tracking == tracking:
                defect.qty = 1
                return defect
        new_defect = Defect()
        self.defects.append()

    def clean_defects(self, characteristic, element_key=None):
        all_failure_modes = characteristic.get_all_failure_modes()
        for defect in self.defects:
            if defect.failure_mode == failure_mode:
                defect.qty = 0
            return True
        return False

    def add_measurement(self, characteristic, value, tracking=None):
        """Add a measurement for characteristic and returns it"""
        pass



class Device(Item):
    __mapper_args__ = {'polymorphic_identity': 'device'}

    def __init__(self, device_model, tracking, **kwargs):
        Item.__init__(self,
                      resource=device_model, tracking=tracking, **kwargs)
        self.bh = None

    def setup(self):
        if not self.resource.pars:
            return None  # No class to load

        resource_pars = self.resource.pars.get()
        if 'class_name' not in resource_pars:
            return None  # No class to load

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


class PartAttribute:
    @hybrid_property
    def part(self):
        if self._parts:
            return self._parts[0]

    @part.setter
    def part(self, part):
        if self._parts:
            self._parts[0] = part
        else:
            self._parts.append(part)



class Defect(Item, PartAttribute):
    __mapper_args__ = {'polymorphic_identity': 'defect'}

    def __init__(self, part, failure_mode, qty=1.0, measurement=None):
        self.part = part
        self.resource = failure_mode
        self.qty = qty
        if measurement is not None:
            self._measuremments.append(measurement)

    @hybrid_property
    def failure_mode(self):
        return self.resource

    @failure_mode.setter
    def failure_mode(self, failure_mode):
        self.resource = failure_mode


class Measurement(Item, PartAttribute):
    __mapper_args__ = {'polymorphic_identity': 'measurement'}
    _defects = relationship(
        'Defect', secondary=ItemLink,
        primaryjoin=Item.id == ItemLink.c.from_item_id,
        secondaryjoin=Defect.id == ItemLink.c.to_item_id,
        backref='_measurements'
    )

    def __init__(self, part, characteristic, value, **kwargs):
        super().__init__(resource=characteristic, **kwargs)
        self.qty = value
        self.part = part


    def evaluate(self, limits, uncertainty=0.0):
        """Evals the measurement against limits and add defect to part if NC"""
        defect = None
        low_limit, high_limit = limits

        if self.qty > high_limit - uncertainty:
            mode_key = 'hi' if self.qty > high_limit else 'shi'

        if self.qty < low_limit + uncertainty:
            mode_key = 'lw' if self.qty < low_limit else 'slw'

        if mode_key:
            failure_mode = self.characteristic.get_or_create_failure_mode(mode_key)
            defect = self.part.add_defect(failure_mode)
            self.defect = defect

        return defect

    @hybrid_property
    def characteristic(self):
        return self.resource

    @hybrid_property
    def defect(self):
        if self._defects:
            self._defects[0]

    @defect.setter
    def defect(self, defect):
        if self._defects:
            self._defects[0] = defect
        else:
            self._defects.append(defect)


class Report(Item):
    __mapper_args__ = {'polymorphic_identity': 'report'}

    parts = relationship('Part', secondary=ItemLink,
                         primaryjoin=Item.id==ItemLink.c.from_item_id,
                         secondaryjoin=Part.id==ItemLink.c.to_item_id)
