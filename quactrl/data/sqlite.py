import os.path
import sqlite3


class TestSaver:
    def __init__(self, file_name=':memory:', clear=False):
        "docstring"
        self.conn = sqlite3.connect(file_name)
        self.c = self.conn.cursor()
        if os.path.exists(file_name) and clear:
            self.clear()
        else:
            self.create_schema()

    def save(self, test):
        self.c = self.conn.cursor()
        part = self.upsert_part(test.part)
        self.insert_test(test)
        for action in test.actions:
            if action.__class__.__name__ == 'Check':
                check = action
                self.insert_check(check)
                for measurement in check.measurements:
                    self.insert_measurement(measurement, check)
                for defect in check.defects:
                    self.insert_defect(defect, check)
            else:
                self.insert_action(action)
        self.conn.commit()

    def create_schema(self):
        self.c.execute(
            """
            CREATE TABLE `Parts`
            ( `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `part_number` TEXT,
            `serial_number` TEXT )
            """
        )
        self.c.execute(
            """
            CREATE TABLE 'Tests'
            (
            'id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'fk_part' INTEGER,
            'started_on' TEXT,
            'finished_on' TEXT,
            'responsible_key' TEXT,
            'state' TEXT
            )
            """
        )
        self.c.execute(
            """
            CREATE TABLE 'Actions'
            (
            'id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'fk_test' INTEGER,
            'started_on' TEXT,
            'finished_on' TEXT,
            'description' TEXT,
            'state' TEXT
            )
            """
        )
        self.c.execute(
            """
            CREATE TABLE 'Measurements'
            (
            'id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'fk_check' INTEGER,
            'char_key' TEXT,
            'tracking' TEXT,
            'value' REAL
            )
            """
        )
        self.c.execute(
            """
            CREATE TABLE 'Defects'
            (
            'id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'fk_check' INTEGER,
            'failure_key' TEXT,
            'tracking' TEXT
            )
            """
        )

        self.conn.commit()

    def clear(self):
        self.c.execute('DELETE * FROM Measurements')
        self.c.execute('DELETE * FROM Defects')
        self.c.execute('DELETE * FROM Actions')
        self.c.execute('DELETE * FROM Tests')
        self.c.execute('DELETE * FROM Parts')
        cursor.commit()

    def upsert_part(self, part):
        self.c.execute(
            'select id from Parts where part_number=? and serial_number=?',
            (part.model.key, part.serial_number)
        )
        result = self.c.fetchone()
        id = result[0] if result else None

        if not id:
            self.c.execute(
                'insert into Parts (part_number, serial_number) values (?, ?)',
                (part.model.key, part.serial_number)
            )
            id = self.c.lastrowid

        part._id = id

    def insert_test(self, test):
        finished_on = test.finished_on.isoformat(' ') if test.finished_on else None
        self.c.execute(
            ('insert into Tests '
             '(fk_part, started_on, finished_on, responsible_key, state) '
             'values (?, ?, ?, ?, ?)'),
            (test.part._id, test.started_on, test.finished_on,
             test.state, test.responsible.key)
        )
        test._id = self.c.lastrowid

    def insert_check(self, check):
        print((check.test._id, check.started_on, check.finished_on,
             check.requirement.description, check.state))
        self.c.execute(
            ('insert into Actions '
             '(fk_test, started_on, finished_on, description, state) '
             'values (?, ?, ?, ?, ?)'),
            (check.test._id, check.started_on, check.finished_on,
             check.requirement.description, check.state)
        )
        check._id = self.c.lastrowid

    def insert_action(self, action):
        self.c.execute(
            ('insert into Actions '
             '(fk_test, started_on, finished_on, description, state) '
             'values (?, ?, ?, ?, ?)'),
            (action.test._id, action.started_on,
             action.finished_on,
             action.step.method_name, action.state)
        )
        action._id = self.c.lastrowid

    def insert_measurement(self, measurement, check):
        self.c.execute(
            ('insert into Measurements '
             '(fk_check, char_key, tracking, value) '
             'values (?, ?, ?, ?)'),
            (check._id, measurement.characteristic.key, measurement.tracking,
             measurement.value)
        )

        measurement._id = self.c.lastrowid

    def insert_defect(self, defect, check):
        self.c.execute(
            ('insert into Defects '
             '(fk_check, failure_key, tracking) '
             'values (? , ?, ?)'),
            (check._id, defect.failure.key, defect.tracking)
        )
        defect._id = self.c.lastrowid
