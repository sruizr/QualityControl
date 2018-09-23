from unittest.mock import Mock, patch
import quactrl.models.operations as o


class An_Operation:

    @patch('quactrl.models.operations.datetime')
    def should_start(self, mock_datetime):
        parent = Mock()
        route = Mock()
        route.steps = []
        responsible = Mock()
        operation = o.Operation(route, parent, responsible)
        part = Mock()
        tester = Mock()
        operation.start(subject=part, tester=tester)

        expected = {'subject': part, 'tester': tester}
        assert operation.inbox == expected
        assert operation.state == 'started'
        mock_datetime.datetime.now.assert_called_with()

    def should_walk_through_its_subops(self):
        parent = Mock()
        route = Mock()
        route.steps = [Mock() for _ in range(3)]
        responsible = Mock()
        operation = o.Operation(route, parent, responsible)

        async_op = route.steps[1].create_operation.return_value
        async_op.state = 'ongoing'
        operation.walk()
        for step in route.steps:
            step.create_operation.assert_called_with(operation)
            op = step.create_operation.return_value
            op.start.assert_called_with()
            op.execute.assert_called_with()
            op.close.assert_called_with()

        async_op.thread.join.assert_called_with()

    def  should_execute(self):
        parent = Mock()
        route = Mock()
        route.method = 'method_name'
        route.method_pars = {'par': 1}
        method = route.get_method.return_value
        responsible = Mock()
        operation = o.Operation(route, parent, responsible)
        operation.state = 'started'

        operation.execute()
        method.assert_called_with(operation, par=1)
        assert operation.state == 'finished'

        # Testing async execution
        operation.state = 'started'
        operation.thread = Mock()

        operation.execute()
        assert operation.state == 'ongoing'

    @patch('quactrl.models.operations.datetime')
    def should_close(self, mock_datetime):
        parent = Mock()
        route = Mock()
        responsible = Mock()
        operation = o.Operation(route, parent, responsible)

        # Other test
        operation.state = 'finished'
        operation.close()
        assert operation.state == 'closed'
        assert operation.finished_on == mock_datetime.datetime.now()

    @patch('quactrl.models.operations.datetime')
    def should_cancel(self, mock_datetime):
        parent = Mock()
        route = Mock()
        responsible = Mock()
        operation = o.Operation(route, parent, responsible)
        operation.state = 'ongoing'
        operation.thread = Mock()

        operation.cancel()
        assert operation.state == 'cancelled'
        assert operation.finished_on == mock_datetime.datetime.now()
        operation.thread.cancel.assert_called_with()

        operation.state = 'walking'
        operation.current_op = Mock()
        operation.cancel()
        operation.current_op.cancel.assert_called_with()
        assert operation._cancel == True


class A_Route:
    def should_insert_into_parent(self):
        parent = Mock()
        parent.steps = []

        route = o.Route(parent=parent)
        assert route in parent.steps
        assert route.sequence == 0

        other = o.Route(parent=parent)
        assert len(parent.steps) == 2
        assert other.sequence == 5

    @patch('quactrl.models.operations.get_function')
    def should_get_method(self, mock_get):
        parent = Mock()
        parent.steps = []
        route = o.Route(parent=parent, method='method_name')

        method = route.get_method()

        mock_get.assert_called_with('method_name')
        assert method == mock_get.return_value


    @patch('quactrl.models.operations.Operation')
    def should_create_operation(self, mock_Operation):
        parent_op = Mock()
        route = o.Route()

        operation = route.create_operation(parent_op)

        mock_Operation.assert_called_with(route, parent_op, None)
        assert operation is mock_Operation.return_value
