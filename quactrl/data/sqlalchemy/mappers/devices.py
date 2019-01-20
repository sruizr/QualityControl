from sqlalchemy.orm import mapper
import quactrl.models.devices as devices
import quactrl.data.sqlalchemy.tables as tables


device_model_mapper = mapper(
    devices.DeviceModel, tables.resource_table
)


device_mapper = mapper(
    devices.Device, tables.item_table
)
