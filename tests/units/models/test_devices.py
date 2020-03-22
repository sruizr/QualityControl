from unittest.mock import patch, Mock
import quactrl.models.devices as devs


class FakeConn:
    def __init__(self, port):
        self.port = port


class FakeDevice:
    def __init__(self, par_1, par_2, **kwargs):
        self.par_1 = par_1
        self.par_2 = par_2
        for key, value in kwargs.items():
            setattr(self, key, value)


class OtherFakeDevice:
    def __init__(self, par_1):
        self.par_1 = par_1


class A_DutFactory:
    def should_provide_duts_from_cavity(self):
        model = Mock()
        model.kwargs = {'a': 1}
        model.args = [1, 3]
        conn_provider = Mock()

        dut_factory = devs.DutFactory(conn_provider)
        dut = dut_factory(model, None)
        conn_provider.assert_called_with()
        model.Device.assert_called_with(conn_provider(), 1, 3, a=1)
        assert dut is model.Device()

        dut = dut_factory(model, 0)
        conn_provider.assert_called_with(0)

class A_MultiplexedDutFactory:
    @patch('quactrl.models.devices.len')
    def should_provide_multiplexed_duts(self, mock_len):
        model = Mock()
        model.kwargs = {}
        model.args = []
        conn_provider = Mock()
        multiplexor_factory = Mock()
        mock_len.return_value  = 3

        dut_factory = devs.MultiplexedDutFactory(conn_provider, multiplexor_factory)
        dut = dut_factory(model, 21)

        conn_provider.assert_called_with(2)
        model.Device.assert_called_with(conn_provider())
        multiplexor_factory.assert_called_with(model.Device(), 21)

        mock_len.return_value = 1

# class A_ConnectionProvider:
#     def should_provide_unique_connection(self):
#         Connection = Mock()
#         port = 'port0'

#         conn_provider = devs.ConnectionProvider(Connection, port=port)
#         conn = conn_provider()

#         Connection.assert_called_with(port)
#         assert conn is Connection()


#     def should_provides_connections_with_multiple_ports(self):
#         Connection = Mock()
#         ports = ['port1', 'port2']

#         conn_provider = devs.ConnectionProvider(Connection, port=ports)
#         conn = conn_provider(1)

#         Connection.assert_called_with(ports[1])
#         assert conn is Connection()


class A_DeviceProvider:
    def should_produces_simple_singleton_devices(self):
        Device = Mock()
        Device.side_effect = [Mock(), Mock()]

        device_provider = devs.DeviceProvider(Device, 1,
                                              tracking='tracking_content',
                                              foo=3)

        device = device_provider()
        other_dev = device_provider()

        assert device is other_dev
        assert device.tracking == 'tracking_content'
        Device.assert_called_with(1, foo=3)


    def should_produce_multiple_singleton_devices(self):
        Device = Mock()
        Device.side_effect = [Mock() for _ in range(3)]
        kwargs = {
            'tracking': 'track',
            'multi_dev_on': 'port',
            'port': [1, 2, 3]
        }

        device_provider = devs.DeviceProvider(Device, 1, **kwargs)

        device = device_provider(0)
        Device.assert_called_with(1, port=1)
        assert device.tracking == 'track'

        other_dev = device_provider(0)
        assert device is other_dev

        other_dev = device_provider(2)
        assert device is not other_dev
        Device.assert_called_with(1, port=3)

        assert len(device_provider) == 3


class A_Toolbox:
    @patch('quactrl.models.devices.get_class')
    def should_process_simple_device(self, mock_get_class):
        device = Mock()
        device.tracking = 'track'
        device.name = 'my_device'
        device.model.class_name = 'FakeDevice'
        device.args = [1]
        device.kwargs = {'foo': 0}

        Device = mock_get_class.return_value

        devices = [device]
        toolbox = devs.Toolbox(devices)

        mock_get_class.assert_called_with('FakeDevice')
        assert type(toolbox.my_device) is devs.DeviceProvider

        device = toolbox.my_device()
        Device.assert_called_with(1, foo=0)
        assert device.tracking == 'track'
