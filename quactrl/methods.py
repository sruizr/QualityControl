from quactrl.domain.do import Device, Part


def gen_device(flow, controller=None):

    device_data = flow.inputs.pop()

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


def gen_part(flow, controller=None):
    item_data = flow.inputs.pop()

    resource_key = item_data.pop('resource_key')
    tracking = item_data.pop('tracking')

    resource, qty = flow.path.out_resources[resource_key]
    part = Part(resource, tracking=tracking, pars=item_data)
    flow.outputs.append((part, qty))


def by_pass(flow, controller=None):
    for _input in flow.inputs:
        flow.outputs.append((_input.item, _input.qty))
