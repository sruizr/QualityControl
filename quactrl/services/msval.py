import quactrl.models.quality as qua
import quactrl.models.operations as op
import quactrl.models.reporting as rpt
import datetime


class MeasureSystemValidation(op.Operation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.control_plan = self.route

    def start(self, **kwargs):
        super().start(**kwargs)

        if self.ms.location != self.control_plan.source and self.started_on < datetime.now():
            self.ms.move(self.ms.location, self.control_plan.source, self)

    def close(self):
        pass


class Service:
    def __init__(self, database, responsible_key):
        self.db = database
        self.responsible = self.db.get_responsible_by_key(responsible_key)

    def select_measure_system(self, ms_tracking, responsible):
        self.measure_system = self.db.get_measure_system(ms_tracking)

        if not self.measure_system:
            raise ItemNotFound(ms_tracking)

    def record_calibration_report(self, content):
        self._validate_content(content)

        report = rpt.Report(form, tracking, content)
        self.measure_system.items.append(report)

        self.validation.start(
            measure_system=self.measure_system,
            calibration_report=report
        )
        try:
            self.validation.walk()
        except:
            self.validate.cancel()


    def get_validation_eval_results(self):
        result = 'started'
        if self.validation.checks:
            for  check in validatio.checks:
                if check.has_failures() then:
                    return False

        return result


    def decide_conformity(self, validation_decision=None, comment=None):
        self.validation.close(validation_decision, comment)
        self.db.commit()

    def show_calibration_data(self):
        return self.calibration_report.content
