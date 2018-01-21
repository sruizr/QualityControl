import datetime


class InspectionController:
    """Controller for accessing to quactrl domain and service inspection"""
    def __init__(self, environment):
        self.env = environment
        self.domain = environment.domain
        self.service = environment.service
        self.view = environment.view
        self.force_batch = self.env.pars.get('force_batch', False)
        self.operator = None
        self._batches = {}
        self.started_on = None
        self.count = 0
        self.finished_on = None

    def open_session(self, operator_key):
        self.service.set_process(self.env.pars['process'])
        self.view.show_welcome()
        self.operator = self.domain.get_operator(operator_key)
        if self.operator is None:
            self.show_error(
                'Operator {} is not valid'.format(operator_key)
                )
            return None
        self.service.set_operator(self.operator)
        self.started_on = datetime.datetime.now()

    def start_batch(self, batch_data, cavity=0):
        self._batches[cavity] = self.domain.get_batch(batch_data['key'],
                                                      batch_data['partnumber'])
        if self.batch[cavity] is None:
            self.show_error(
                'Batch {} for partnumber {} is not valid'.format(
                    batch_data['key'], batch_data['partnumber']
                    )
                )
            return None
        self.service.setup_batch(self._batches[cavity], cavity)

    def start_test(self, item_data, cavity=0):
        if self.operator is None:
            self.view.show_error("Operator is not identified")
            return None
        if self._batches.get(cavity) is None:
            self.view.show_error('Batch is not selected')
            return None

        item = self.domain.get_item(item_data)
        new_batch = item.batch != self._batches.get(cavity)

        if new_batch:
            if self.force_batch:
                self.view.show_error(
                    "Item {} is_not from batch {}".format(item_data.sn,
                                                          self.batch_number
                                                          )
                    )
                return None
            else:
                self._batches[cavity] = item.batch
                self.service.set_batch(item.batch)

        test = self.service.receive_part(item, cavity)
        if test:
            self.view.show_test_started(test)

    def test_is_finished(self, test):
        self.count += 1
        self.view.show_resume(test)

    def close_session(self):
        self.show_resume_session()

    def close(self):
        self.view.show_bye_bye()
