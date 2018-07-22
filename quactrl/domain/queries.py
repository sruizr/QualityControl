from quactrl.domain.persistence import dal
import quactrl.domain.nodes as nodes
import quactrl.domain.resources as resources
import quactrl.domain.items as items
import quactrl.domain.flows as flows
import quactrl.domain.base as base
import quactrl.domain.paths as paths


def get_location(key):
    session = dal.Session()
    return session.query(nodes.Location).filter_by(key=key).one_or_none()

def get_resource(**kargs):
    pass

# Generated from managers.Tester
def get_control_plan_by(location_key, part_model_key):
    session = dal.Session()

    session.query(paths.ControlPlan).join()


def get_responsible_by(key):
    session = dal.Session()
    responsible = (
        session.query(nodes.Person).filter_by(key='key').one_or_none()
    )

    return responsible


def get_or_create_part(part_info, location_key):
    session = dal.Session()
    tracking = part_info['tracking']
    part_number = part_info['number']

    Part = items.Part
    PartModel = resources.PartModel
    Token = flows.Token
    Node = base.Node
    part = (
        session.query(Part).join(PartModel).join(Token).join(Node)
        .filter(
            Node.key == location_key,
            Token.state == 'avalaible',
            Part.tracking == tracking,
            PartModel.key == part_number)
        .one_or_none()
    )

    if part:
        return part
    else:
        # Create part
        part_model = dal.get('part_model', key=part_info['part_number'])
        part = items.Part(tracking=part_info, resource=part_model)
        location = dal.get('location', key=location_key)
        part.locate_at(location)
        session.add(part)
        return part


def get_devices_by_location(key):
    session = dal.Session()
    Device, Token, Node = (items.Device, base.Token, base.Node)
    query = session.query(Device).join(Token).join(Node).filter(
        Node.key == key,
        Token.consumer == None
    ).order_by(Device.tracking)

    return query.all()

def get_process_by(key):
    session = dal.Session()
    qry = session.query(resources.Process).filter(resources.Process.key == key)

    return qry.one()

    # def get_item_by_sn(self, serial_number):
    #     if not self.session:
    #         self.open_session()

    # def get_or_create_dut(self, **kwargs):
    #     """Return a fully functional dut for testing"""
    #     pass

    # def get_person(self, key, session=None):
    #     """Get operator from data layer if not exist it return None"""
    #     session = self.dal.Session() if session is None else session

    #     return session.query(Person).filter_by(key=key).first()

    # def get_tokens_by_ids(self, ids, session=None):
    #     session = self.dal.Session() if session is None else session
    #     results = session.query(Token).filter(Token.id.in_(ids)).all()
    #     return results


    # def get_avalaible_token_ids(self, location_key, item_args, session=None):
    #     session = self.dal.Session() if session is None else session

    #     filters = [Token.state == 'avalaible', Node.key == location_key]
    #     qry = session.query(Token.id).join(Node).join(Item)

    #     if 'resource_key' in item_args:
    #         qry = qry.join(Resource)
    #         filters.append(Resource.key == item_args['resource_key'])
    #     if 'tracking' in item_args:
    #         filters.append(Item.tracking == item_args['tracking'])

    #     token_ids = [value[0] for value in qry.filter(*filters).all()]

    #     return token_ids

    # # def create_dut(self, item):
    # #     """Returns a fully functional device"""
    # #     if item.resource.pars is None:
    # #         return item

    # #     device_name = item.resource.key
    # #     pars = item.resource.pars.get()
    # #     if not device_name in self._duts:
    # #         class_name = pars['class_name']
    # #         modules = class_name.split('.')
    # #         module = importlib.import_module('.'.join(modules[:-1]))
    # #         Device = getattr(module, modules[-1], None)
    # #         self._duts[device_name] = (Device, pars)

    # #     Device, pars = self._devices.get(device_name)
    # #     return Device(item, pars)

    # # def get_location(self, key):
    # #     session = self.dal.Session()
    # #     return session.query(Location).filter(Location.key == key).one()


    # def get_devices_by_location(self, location_key, session=None):
    #     """Return a dict with all devices of a location"""
    #     session = self.dal.Session() if session is None else session

    #     query = session.query(Device).join(Token).join(Node).filter(
    #         Node.key == location_key,
    #         Token.state == 'avalaible'
    #         ).order_by(Device.tracking)

    #     devices_by_tracking = {}
    #     devices_by_key = {}

    #     for device in query.all():
    #         device.setup()
    #         tracking = device.tracking
    #         devices_by_tracking[tracking] = device

    #         key = device.resource.key
    #         if key in devices_by_key:
    #             if type(devices_by_key[key]) is dict:
    #                 devices_by_key[key][tracking] = device
    #             else:
    #                 first_device = devices_by_key[key]
    #                 devices_by_key[key] = {
    #                     first_device.tracking: first_device,
    #                     device.tracking: device
    #                     }
    #         else:
    #             devices_by_key[key] = device

    #     for device in devices_by_tracking.values():
    #         device.assembly(devices_by_tracking)

    #     return devices_by_key

    # # def get_item(self, serial_number, resource_key):
    # #     return self.dal.session.query(Item).join(Resource).filter(
    # #         Dut.tracking == serial_number,
    # #         Resource.key == resource_key
    # #         ).first()

    # # def create_dut(self, resource_key, serial_number):
    # #     resource = self.dal.session.query(Resource).filter(
    # #         Resource.key == resource_key).first()

    # #     return Dut(resource, tracking= serial_number)

    #  # def get_dut_at_location(self, serial_number, location_key):
    #  #    qry = self.dal.session.query(Dut).join(Movement).filter(
    #  #        Dut.tracking == serial_number,
    #  #        Movement.to_node is None,
    #  #        Node.key == location_key
    #  #        )
    #  #    return qry.first()

def get_stocks_by_node(self, node, session=None):
    session = self.dal.Session() if session is None else session

    qry = session.query(Token).filter(
        Token.node == node,
        Token.state == 'avalaible'
        )

    return qry.all()
