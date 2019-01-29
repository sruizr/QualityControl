from sqlalchemy.orm import mapper, synonym
import quactrl.models.devices as devices
import quactrl.models.core as core
import quactrl.models.quality as qua
import quactrl.data.sqlalchemy.tables as tables


mapper(devices.DeviceModel, inherits=devices.Resource,
       polymorphic_identity='device_model')


mapper(devices.Device, inherits=qua.Subject,
       polymorphic_identity='device',
       properties={
           'model': synonym('resource')
       })
