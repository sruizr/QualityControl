import cherrypy
from quactrl.managers.devices import DeviceManager, DeviceProxy
from quactrl.domain.data import dal


@cherrypy.expose
class DeviceResource:
    """Server devices as repository using API REST"""
    def __init__(self):
        self.device_manager = DeviceManager()

    @cherrypy.tools.json_out()
    @cherrypy.popargs('key')
    def GET(self, key=None):
        """Get device status"""
        if key in self.device_manager.devices.keys():
            device = self.device_manager.devices[key]
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
                status = 'iddle' if self.device_manager.devices[key].is_bussy() else 'waiting'
                return {'status': status}
        else:
            cherrypy.response.status = 404
            return  {'status': 'absent'}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, key, tracking=None):
        """Sends to command to device"""

        return None

    @cherrypy.popargs('location')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self, location=None):
        """Loads  devices onto repository"""
        pars = cherrypy.request.json
        if pars.get('class_name'):  # Device pars for loading
            self.device_manager[pars['name']] = DeviceProxy(
                pars['name'],
                pars['tracking'],
                pars
            )
        else:
            if location is None:  # Connection to database
                dal.connect(pars['connection_string'])
            else:
                if dal.is_connected():
                    self.device_manager.load_devs_from(location)
                else:
                    cherrypy.response.status = 500

    @cherrypy.popargs('key')
    def DELETE(self, key=None):
        """Remove devices from repository"""
        if key is None:
            keys = list(self.device_manager.devices.keys())
            for key in keys:
                del self.device_manager.devices[key]
        else:
            if key in self.device_manager.devices.keys():
                del self.device_manager.devices[key]
            else:
                cherrypy.response.status = 404
