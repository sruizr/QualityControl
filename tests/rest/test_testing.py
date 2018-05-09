            'type': 'Measure',
            'characteristic': {'key': 'char'},
            'value': 1.2
        }
        assert measure_data == expected

    def should_parse_characteristic(self):
        characteristic = Mock()
        characteristic.description = 'char description'
        characteristic.key = 'char_key'
        char_data = self.parser.parse_characteristic(characteristic)

        expected = {'type': 'Characteristic',
                    'description': 'Char description',
                    'key': 'char_key'
        }
        assert char_data == expected

    def should_parse_defect(self):
        defect = Mock()
        defect.description = 'defect description'
        defect.characteristic.key = 'char'

        defect_data = self.parser.parse_defect(defect)
        expected = {
            'type': 'Defect',
            'description': 'Defect description',
            'char_key': 'char'
        }

class An_AuTestResource:
    def setup_class(cls):
        # Patch runner
        cls._runner_patcher = patch(
            'quactrl.services.testing.AuTestResource.runner'
        )
        cls._parser_patcher = patch(
            'quactrl.services.testing.AuTestResource.parser')

        cls.runner = cls._runner_patcher.start()
        cls.parser = cls._parser_patcher.start()
        conf = {'/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True
        }}
        cherrypy.tree.mount(AuTestResource(), '/', conf)
        cls.url = 'http://127.0.0.1:8080'
        cherrypy.engine.start()

    def teardown_class(cls):
        cls._runner_patcher.stop()
        cls._parser_patcher.stop()
        cherrypy.engine.exit()

    def setup_method(self, method):
        self.parser.parse = lambda obj: {'key': obj.key}

    def should_return_open_tests(self):
        self.runner.tests = [Mock(key='test_{}'.format(_n))
                             for _n in range(2)]

        # Get all tests
        response = requests.get(self.url)

        assert response.status_code == 200
        expected= [
            {'key': 'test_0'},
            {'key': 'test_1'}]
        assert response.json() == expected

        response = requests.get(self.url + '/1')
        assert response.status_code == 200
        assert response.json() == expected[0]

    def should_setup_from_PUT_request(self):
        self.runner.set_location.side_effect = [None, Exception()]

        url = self.url + '/fake'
        response = requests.put(url)

        assert response.status_code == 200
        expected = {'status': 'done',
                    'location': 'fake'}
        assert response.json() == expected

        response = requests.put(self.url + '/invalid')
        assert response.status_code == 500

    def should_begin_test_from_part_information(self):
        json_req = {
            'tracking': '123456789',
            'part_name': 'part_name',
            'part_number': 'part_number',
            'responsible_key': 'sruiz',
            'cavity': 1
        }

        response = requests.post(self.url,
                                 json=json_req)

        assert response.status_code == 200
        expected = {'key': 'test_0'}
        assert response.json() == expected

        json_req['cavity'] = 2

        response = requests.post(self.url, json=json_req)
        assert response.json() == {'key': 'test_1'}
        self.runner.start_test.assert_called_with(
            {'tracking': '123456789',
             'part_name': 'part_name',
             'part_number': 'part_number'},
            'sruiz',
            cavity=2)

    def should_stop_any_test(self):
        response = requests.delete(self.url + '/1')
        assert response.status_code == 200
        self.runner.stop.assert_called_with(0)

        response = requests.delete(self.url)
        assert response.status_code == 200
        self.runner.stop.assert_called_with()

    def should_report_events(self):
        self.runner.events = Queue()
        for _n in range(2):
            event = Mock(key='event_{}'.format(_n))
            self.runner.events.put(event)

        response = requests.get(self.url + '/events')
        assert response.status_code == 200

        expected = [{'key': 'event_0'}, {'key': 'event_1'}]

        assert response.json() == expected
