class Device:
    """Base class for device generation"""
    def __init__(self, **pars):
        """Blank device with attributes generated from pars
        """
        if pars:
            for key, value in pars.items():
                setattr(self, key, value)

    def assembly(self, devices):
        """Assemble devices to other devices as subsystems
        Args:
            devices(dict): dictionary of devices where key is tracking numbers
        """
        if hasattr(self, 'connected_to'):
            for key, tracking in self.connected_to.items():
                if type(tracking) is list:
                    att_value = [devices[value] for value in tracking]
                else:
                    att_value = devices[tracking]
                setattr(self, key, att_value)
