from quactrl.data.sqlalchemy.mappers import core, devices
from quactrl.models.devices import DeviceModel, Device
from . import TestMapper


class A_DeviceModule(TestMapper):
    def should_map_device_and_device_models(self):
        session = self.Session()

        device_model = DeviceModel('dev_key', 'device',
                                   'A silly device', {'par': 1})
        session.add(device_model)

        device = Device(device_model, '123456789')
        session.add(device)

        session.commit()

        other_session = self.Session()
        assert other_session != session

        other_device = other_session.query(Device).first()
        assert device != other_device
        assert other_device.model.pars['par'] == 1
