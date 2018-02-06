class DeviceBase:
    def __init__(self, **pars):
        if pars:
            for key, value in pars.items():
                setattr(self, key, value)

    def assembly(self, devices):
        if hasattr(self, 'connected_to'):
            for key, value in self.connected_to.items():
                if type(value) is list:
                    att_value = [devices[tracking] for tracking in value]
                else:
                    att_value = devices[value]
                setattr(self, key, att_value)
