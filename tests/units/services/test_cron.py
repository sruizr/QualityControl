from unittest.mock import Mock, patch
import datetime
from quactrl.services.cron import Service


class A_Cron_Service:
    @patch('quactrl.services.cron.datetime')
    def should_review_all_planned_flows(self, mock_datetime):
        data = Mock()
        now = mock_datetime.now.return_value = datetime.datetime(1,1,1)
        service = Service(data)

        data.flows().get_planned_flows.assert_called_with(
            now + datetime.timedelta(weeks=4)
        )


    def should_realize_planned_movements(self):
        se
