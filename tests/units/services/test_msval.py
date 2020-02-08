import  quactrl.services.msval as msval
from unittest.mock import Mock, call


def test_record_calibration_results():
    action = Mock()

    msval.record_calibration_results(action)

    assert action.measurement_system.reports[-1].content == {}
    assert action.measurement_systems.report[-1].tracking == 'reportId'


def test_eval_measurement_error_at_ms():
    check = Mock()

    # measurement_system contents all calibration reports
    check.measurement_system.reports = [Mock() for _ in range(2)]
    # The system will evaluate the last calibration report,
    # I mock its content
    check.measurement_system.reports[-1].content = {
        'points': [
            # Structure is point label | reference value | uncertainty | measured values (if there are several channels)
            ('pt1', 1, 0.5, 1.2, 1.3),
            ('pt2', 2, 0.5, 2.4, 2.5)
        ]
    }

    # calling function to test
    msval.eval_measurement_error(check)

    # Assert measurements are added to check
    expected_calls = [
        call(0.2, check.control.requirement, check.measurement_system, 'pt1#0'),
        call(0.3, check.control.requirement, check.measurement_system, 'pt1#1'),
        call(0.4, check.control.requirement, check.measurement_system, 'pt2#0'),
        call(0.5, check.control.requirement, check.measurement_system, 'pt2#1')
    ]

    for expected_call in expected_calls:
        assert expected_call in check.add_measurement.mock_calls


def test_eval_error_drift_at_ms():
    check = Mock()

    # measurement_system contents all calibration reports
    check.measurement_system.reports = [Mock() for _ in range(2)]
    # The system will evaluate the last calibration report, and previous one
    # I mock theirs contents
    check.measurement_system.reports[-2].content = {
        'points': [
            ('pt1', 1.1, 0.5, 1.2, 1.3),
            ('pt2', 2.3, 0.5, 2.4, 2.5)
        ]
    }

    check.measurement_system.reports[-1].content = {
        'points': [
            ('pt1', 1, 0.5, 1.2, 1.3),
            ('pt2', 2, 0.5, 2.4, 2.5)
        ]
    }

    # calling function to test
    msval.eval_error_drift_at_ms(check)

    # Assert measurements are added to check
    expected_calls = [
        call(0.1, check.control.requirement, check.measurement_system, 'pt1#0'),
        call(0.1, check.control.requirement, check.measurement_system, 'pt1#1'),
        call(0.3, check.control.requirement, check.measurement_system, 'pt2#0'),
        call(0.4, check.control.requirement, check.measurement_system, 'pt2#1')
    ]

    for expected_call in expected_calls:
        assert expected_call in  check.add_measurement.mock_calls


def test_eval_test_uncertainty():
    check = Mock()

    # measurement_system contents all calibration reports
    check.measurement_system.reports = [Mock() for _ in range(2)]
    # The system will evaluate the last calibration report,
    # I mock its content
    check.measurement_system.reports[-1].content = {
        'points': [
            # Structure is point label | reference value | uncertainty | measured values (if there are several channels)
            ('pt1', 1, 0.3, 1.2, 1.3),
            ('pt2', 2, 0.5, 2.4, 2.5)
        ]
    }

    # calling function to test
    msval.eval_test_uncertainty(check)

    # Assert measurements are added to check
    expected_calls = [
        call(0.3, check.control.requirement, check.measurement_system, 'pt1'),
        call(0.5, check.control.requirement, check.measurement_system, 'pt2')
    ]

    for expected_call in expected_calls:
        assert expected_call in check.add_measurement.mock_calls


def test_responsible_decision():
    # This method should confirm  results of automatic validation



def A_MeasureSystemValidation:
    def should_finish_evaluating_re():
        pass
