import datetime
from types import MethodType


class InspectionController:
    """Controller for accessing to quactrl domain and service inspection"""
    def __init__(self, environment):
        self.env = environment
        self.force_batch = self.env.pars.get('force_batch', False)
        self.dal = environment.dal

        self.service = environment.service
        self.service.set_process(self.env.pars['process'])
        self.view = environment.view

        self.operator = None
        self.session_status = None

    def open_session(self):
        """Open a session by a user operator"""

        self.session_status = {key: 0 for key in ['OK', 'NOK']}
        self.session_status['started_on'] = datetime.datetime.now()

        operator_label = self.view.read_operator()
        if operator_label == '':
            self.close()

        operator_data = self.validate_operator_label(operator_label)
        if not operator_data:
            self.view.show_error(
                'incorrect_operator_label', operator_label=operator_label
                )
            self.open_session()

        self.operator = self.dal.get_operator(operator_key)
        if self.operator is None:
            self.view.show_error('operator_not_found',
                                 operator_key=operator_key)
            self.open_session()

        self.service.set_operator(self.operator)
        self.started_on = datetime.datetime.now()

        if self.force_batch:
            self.start_batch()

    def start_batch(self, batch_data, cavity=0):
        batch_label = self.view.read_batch()
        batch_data = self.validate_batch_label(batch_label)
        if type(batch_data) is str:
            self.show_error('incorrect_batch_label', batch_label=batch_label)
            return None

        self._batches[cavity] = self.dal.get_batch(batch_data['key'],
                                                      batch_data['partnumber'])
        if self.batch[cavity] is None:
            self.show_error(
                'Batch {} for partnumber {} is not valid'.format(
                    batch_data['key'], batch_data['partnumber']
                    )
                )
            return None
        self.service.setup_batch(self._batches[cavity], cavity)

    def start_test(self, cavity=0):
        item_label = self.view.read_item()
        if item_label == '':
            if self.force_batch:
                self.start_batch()
            else:
                self.open_session()
            return None

        item_data = self.validate_item_label(item_label)
        if not item_data:
            self.show_error('incorrect_item_label', item_label=item_data)
            return self.start_test()

        batch_number = self.service.get_current_batch_number(cavity)

        if item_data['batch_number'] != batch_number:
            if self.force_batch:
                self.show_error('incompatible_item', item_label=item_label,
                                batch_number=batch_number
                                )
                return self.start_test()
            else:
                batch = self.dal.get_batch(item_data['batch_number'],
                                           item_data['partnumber'])
                self.service.set_batch(batch, cavity)

        item = self.dal.get_item(item_data)
        if item is None:
            self.show_error('item_not_got', item_label=item_label)
            return self.start_test()

        self.test = self.service.receive_part(item, cavity)
        if self.test:
            self.view.test_started(self.test)

    def test_finished(self, test):
        if test.result == 'pass':
            self.session_status['OK'] += 1
        else:
            self.session_status['NOK'] += 1
        self.view.test_finished(test)

    def check_finished(self, check):
        pass

    def close_session(self):
        """Ends session executed by an operator"""
        self.session_status['finished_on'] = datetime.datetime.now()
        self.session_status['time'] = (
            self.session_status['finished_on'] -
            self.session_status['started_on']
            ).total_seconds() / 60
        self.show_resume_session(self.session_status)

        # Request to open a new session
        self.open_session()

    def close(self):
        """Close application using the controller"""
        self.service.stop()
        self.env.app.stop()

    def set_validations(self, **kwargs):
        """Sets validation methods, to be loaded externally"""
        self.validate_batch_label = MethodType(kwargs['batch_label'], self)
        self.validate_item_label = MethodType(kwargs['item_label'], self)
        self.validate_operator_label = MethodType(kwargs['operator_label'], self)
