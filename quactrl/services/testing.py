import threading
import sys
import traceback
from queue import Queue
from quactrl.models.devices import Toolbox
from quactrl.data import NotFoundPath, NotFoundItem, NotFoundResource
import quactrl.models.operations as op
import quactrl.models.products as prd
from quactrl.models.quality import DefectFound
import logging


logger = logging.getLogger(__name__)


class WrongLocationError(Exception):
    pass


class IncorrectSetup(Exception):
    pass


class InspectorException(Exception):
    pass


class Service:
    """Test parts from a location"""
    def __init__(self, database, location, till_first_failure=True):

        self.db = database
        self.tff = till_first_failure
        self.location_key = location

        self.events = {}
        self.inspectors = {}
        self._lock = threading.Lock()

        all_devices = self.db.Devices().get_all_from(self.location_key)
        logger.info('Sesssion on main is {}'.format(self.db.Session()))
        logger.info('Sesssion on main is {}'.format(self.db.Session()))
        self.toolbox = Toolbox(all_devices)

    @property
    def tests(self):
        """List tests by cavity"""
        return {cavity: inspector.test
                for cavity, inspector in self.inspectors.items()}

    def start(self, cavities):
        """Start the testing service from cavity
        """
        if type(cavities) is int:
            cavities = [cavities]
        for cavity in cavities:
            self.start_inspector(cavity)

    def start_inspector(self, cavity=None):
        """Start a cavity asigning an inspector
        """
        if type(cavity) is list:
            for cavity_ in cavity:
                self.start(cavity_)
        elif cavity in self.inspectors:
            self.restart_inspector(cavity)
        else:
            self.inspectors[cavity] = inspector = Inspector(
                self.db, self.toolbox,
                self.location_key, cavity, self.tff
            )
            self.events[cavity] = []
            inspector.setDaemon(True)
            inspector.start()

    def stop_inspector(self, cavity=None):
        """Stop a concrete inspector or all inspectors"""
        if cavity in self.inspectors.keys():
            inspector = self.inspectors.pop(cavity)
            return inspector.stop()
        elif cavity is None:  # All cavities will stop
            pending_orders = {}
            cavities = list(self.inspectors.keys())
            for cavity in cavities:
                inspector = self.inspectors.pop(cavity)
                if inspector:
                    pending_orders[cavity] = inspector.stop()
            return pending_orders

    @property
    def active_cavities(self):
        return list(self.inspectors.keys())

    def restart_inspector(self, cavity=None, reinsert_orders=True):
        """Restart cavity inspection, all if None
        """
        if cavity in self.active_cavities:
            pending_orders = self.stop_inspector(cavity)
            self.start_inspector(cavity)

            if reinsert_orders:
                for order in pending_orders:
                    self.inspectors[cavity].orders.put(order)
            else:
                return pending_orders

        elif cavity is None:  # All active cavities will restart
            all_orders = {}
            for cavity in self.active_cavities:
                pending_orders = self.restart_inspector(cavity,
                                                        reinsert_orders)
                if not reinsert_orders:
                    all_orders[cavity] = pending_orders
            if not reinsert_orders:
                return all_orders

    def stack_part(self, part_info, responsible_key, cavity=None):
        """Start part for testing on an order process parameters"""
        inspector = self.inspectors[cavity]
        inspector.orders.put((part_info, responsible_key))
        print('Part info is:{}'.format(part_info))
    # def notify(self, info, cavity=None):
    #     """Transfer notification from client to inspector"""
    #     self.inspectors[cavity].notify(info)

    def get_events(self, cavity=None):
        """Get events from inspector from current test"""
        if cavity not in self.active_cavities:
            for _cavity in self.active_cavities:
                self.get_last_events(_cavity)
            return self.events
        else:
            self.get_last_events(cavity)
            return self.events.get(cavity)

    def get_last_events(self, cavity=None):
        """Retrieve last events since previous call
        """
        if cavity not in self.active_cavities:  # Asking to all cavities
            last_events = {}
            for _cavity in self.active_cavities:
                last_events[_cavity] = self.get_last_events(_cavity)
        else:
            last_events = self.inspectors[cavity].get_last_events()
            if self.test_has_finished(cavity) and last_events:
                self.events[cavity] = last_events
            else:
                self.events[cavity].extend(last_events)

        return last_events

    def test_has_finished(self, cavity):
        if cavity not in self.events:
            return True

        if not self.events[cavity]:
            return True

        event = self.events[cavity][-1]
        is_finished = event[0] in ('success', 'failed', 'cancelled')
        is_finished &= event[1].__class__.__name__ == 'Test'
        return is_finished

    def __del__(self):
        for inspector in self.inspectors.values():
            inspector.stop()


class Inspector(threading.Thread):
    """Inspector of one cavity sharing some devices on a location
    """
    def __init__(self, database, toolbox, location_key,
                 cavity=None, tff=True):
        """Args:
        database(Container): Persistence layer container of providers
        toolbox(Container): Container of devices
        location_key: where is located the test station and all its devices
        cavity: cavity number, None is the station is not multicavity
        tff(Boolean): Till first failure, stops test when first failure is found
        """
        name = 'Inspector'
        if cavity is not None:
            name += '_{}'.format(cavity)
        super().__init__(name=name)

        self.db = database
        self.toolbox = toolbox
        self.location_key = location_key
        self.cavity = cavity
        self.tff = tff

        # Inputs and Outputs of inspector
        self.orders = Queue()
        self.events = Queue()
        self.state = 'avalaible'

        # Batch variables
        self.responsible = None
        self.part_model = None
        self.part = None
        self.control_plan = None
        self.test = None

        self._stop_event = threading.Event()

    def set_responsible(self, responsible_key):
        """Loads responsible if it has changed
        """
        if self.responsible is None or self.responsible.key != responsible_key:
            self.responsible = self.db.Persons().get(responsible_key)

    def set_part_model(self, part_number):
        if (self.part_model is None
                or self.part_model.key != part_number):
            self.part_model = self.db.PartModels().get(part_number)
            if self.part_model is None:
                raise NotFoundResource('Not found part model for partnumber{}'.format(part_number))

        if (self.control_plan is None
            or self.part_model not in
            self.control_plan.outputs):
            self.control_plan = (self.db.ControlPlans()
                                 .get_by(self.part_model, self.location))
            if self.control_plan is None:
                raise NotFoundPath('Not found control plan for {}'.format(part_number))


    def run(self):
        """Thread activation processing order by order"""
        self.location = self.db.Locations().get(self.location_key)
        self.devices = {device.tracking: device
                        for device in self.db.Devices().get_all_from(self.location_key)}

        while not self._stop_event.is_set():
            try:
                self.state = 'idle'
                logger.info('Inspector {} is idle'.format(self.name))
                order = self.orders.get()
                if order is None:
                    self.orders.task_done()
                    break
                else:
                    self.state = 'busy'
                    self.run_test(order)
                    self.orders.task_done()
                    logger.info('Inspector {} has finished'.format(self.name))
            except Exception as e:
                trc = sys.exc_info()
                self.update('loop_error', e, traceback.format_tb(trc[2]))
                logger.exception(e)
                raise e
        logger.info('Inspector {} has stopped'.format(self.name))
        self.state = 'stopped'

    def get_part(self, serial_number, pars):
        """Get part from data layer if exist or create a new one
        """

        part = self.db.Parts().get_by(self.part_model, serial_number)
        if part and part.location != self.location:
            raise WrongLocationError(
                'Part {} with sn {} found on {}'.format(
                    part.model.key, part.tracking, part.location.key
                )
            )

        if part is None:
            part = prd.Part(self.part_model, serial_number,
                            pars=pars)

        if part.model.is_device():
            connection = self.toolbox.modbus_conn()
            connection = connection if self.cavity is None \
                else connection[self.cavity]
            part.set_dut(connection)

        return part

    def run_test(self, order):
        """Process a full test  from an order
        """
        try:
            logger.info('Init testing on cavity {}'.format(self.cavity))
            part_info, responsible_key = order
            self.set_responsible(responsible_key)

            part_number = part_info.pop('part_number')
            self.set_part_model(part_number)
            serial_number = part_info.pop('serial_number')
            self.part = part = self.get_part(serial_number, part_info)
            self.test = test = self.control_plan.implement(self.responsible,
                                                           self.update)

            self.db.Tests().add(test)
            self.db.Parts().add(part)
            logger.info('Test has been added on cavity {}'.format(self.cavity))
            test.start(part=part, toolbox=self.toolbox, devices=self.devices,
                       cavity=self.cavity, tff=self.tff)
            try:
                if part.dut and hasattr(part.dut, 'supply_voltage'):
                    self.toolbox.dyncir().switch_on_dut(
                        voltage=part.dut.supply_voltage,
                        wait_after=1, cavity=self.cavity
                    )
                test.walk()
                test.execute()
                test.close()
            except DefectFound:
                test.close()
            except Exception as e:
                logger.exception(e)
                trc = sys.exc_info()
                self.update('test_error', e, traceback.format_tb(trc[2]))
                test.cancel()
            finally:
                self.db.Session().commit()
                if part.dut and hasattr(part.dut, 'supply_voltage'):
                    self.toolbox.dyncir().switch_off_dut(
                        voltage=part.dut.supply_voltage,
                        wait_after=0, cavity=self.cavity
                    )
                self.part = None
        except Exception as e:
            self.part = None
            trc = sys.exc_info()
            self.update('crash', e, traceback.format_tb(trc[2]))
            raise e

    def update(self, state, obj, *args):
        """Receive from test notications of states
        """
        self.events.put(
            [state, obj] + list(args)
        )

    def stop(self):
        """Stop thread and return unprocessed orders"""
        pending_orders = []
        self._stop_event.set()

        if self.orders.qsize() != 0:
            while not self.orders.empty():
                pending_orders.append(self.orders.get())
        else:
            self.orders.put(None)

        return pending_orders

    def answer(self, **kwargs):
        if hasattr(self.test, 'question'):
            self.test.question.answer(**kwargs)

    def get_last_events(self):
        """Retrieve a list of last events of current test
        """
        events = []
        for _ in range(self.events.qsize()):
            event = self.events.get()
            events.append(event)
            if event[0] in ('success', 'failed', 'cancelled') \
               and event[1].__class__.__name__ == 'Test':
                break

        return events

    def cancel(self):
        if self.state == 'busy':
            self.test.cancel()
