from datetime import timedelta, datetime
import logging


logger = logging.getLogger(__name__)


class Messenger:
    pass



class UpdateMovements:
    def __init__(self, database, messenger=None):
        self.db = database
        self.messenger = messenger

    def _query_elapsed_planned_flows(self):
        now = datetime.now()
        return self.db.flows().get_planned_flows_till(now)

    def _query_next_planned_flows(self):
        next_four_weeks = datetime.now() + timedelta(weeks=4)
        return self.db.flows().get_planned_flows_till(next_four_weeks)

    def run(self):
        elapsed_flows = self._query_elapsed_planned_flows()
        for flow in elapsed_flows:
            pars = flow.path.method_pars
            items = self.db.items().get_by_tracking(pars['tracking'])
            try:
                flow.start(items)
                flow.execute()
                flow.close()
            except:
                flow.cancel()

        if self.messenger:
            next_flows = self._query_next_planned_flows(self)
            for flow in next_flows:
                pars = flow.path.method_pars
                if 'notify' in pars:
                    items = self.db.items().get_by_tracking(pars['tracking'])
                    is_sent = self.messenger.send(flow, items, pars['notify'])
                    if is_sent:
                        logger.info('Sent message for items {} to {}'.format(pars['tracking'], pars['notify']['to']))
