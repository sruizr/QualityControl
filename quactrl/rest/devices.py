import cherrypy
from quactrl.managers.devices import DeviceManager, DeviceProxy
from quactrl.domain.persistence import dal


@cherrypy.expose
class DeviceResource:
    """Server devices as repository using API REST"""
    def __init__(self):
        self.manager = DeviceManager()

    @cherrypy.tools.json_out()
    @cherrypy.popargs('key')
    def GET(self, key=None):
        """Get device status"""
        if key in self.manager.devices.keys():
            device = self.manager.devices[key]
            if type(device) is dict:
                result = {}
                for key, _device in device.items():
                    status = (
                        'iddle' if _device.is_bussy()
                        else 'waiting'
                    )
                    result[key] = {'status': status}

                return result
            else:
                status = ('iddle' if self.manager.devices[key].is_bussy()
                          else 'waiting')
                return {'status': status}
        else:
            cherrypy.response.status = 404
            return  {'status': 'absent'}

    @cherrypy.popargs('device_key', 'action')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, device_key, action, tracking=None):
        """Send command to device and return result"""
        device = self.manager.devices[device_key]
        if type(device) is dict:  # Many devices with the same key
            if tracking is None:  # None concrete device!
                cherrypy.response.status = 405
                return
            else:
                device = device[tracking]

        method = getattr(device, action)

        if cherrypy.request.json:
            args, kawrgs = cherrypy.request.json
            try:
                result = method(*args, **kawrgs)
                return result
            except Exception:
                cherrypy.response.status = 405
        else:
            try:
                result = method()
                return result
            except Exception:
                cherrypy.response.statuse = 405

    @cherrypy.popargs('location')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self, location=None):
        """Loads  devices onto repository"""
        pars = cherrypy.request.json
        if pars.get('class_name'):  # Device pars for loading
            self.manager[pars['name']] = DeviceProxy(
                pars['name'],
                pars['tracking'],
                pars
            )
        else:

            if location is None:  # Connection to database
                success = dal.connect(pars['connection_string'])
                if success:
                    return
                else:
                    cherrypy.response.status = 406
            else:
                if dal.is_connected():
                    self.manager.load_devs_from(location)
                else:
                    cherrypy.response.status = 500

    @cherrypy.popargs('key')
    def DELETE(self, key=None):
        """Remove devices from repository"""
        if key is None:
            keys = list(self.manager.devices.keys())
            for key in keys:
                del self.manager.devices[key]
        else:
            if key in self.manager.devices.keys():
                del self.manager.devices[key]
            else:
                cherrypy.response.status = 404
