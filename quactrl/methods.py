from quactrl.domain.do import Device


def gen_device(flow, controller=None):

    device_data = flow.inputs[0]

    resource_key = device_data.pop('resource_key')
    tracking = device_data.pop('tracking')
    qty = device_data.pop('qty', 1.0)

    out_resources = flow.path.out_resources
    expected_output = out_resources[resource_key]

    device = Device(expected_output[0],
                    tracking, pars=device_data)

    if controller:
        controller.notify('DeviceCreated', device=device)

    flow.outputs.append((device, qty))
