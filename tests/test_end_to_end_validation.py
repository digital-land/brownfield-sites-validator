import os
import pytest

from pathlib import Path
from application.validation.validator import validate_file


@pytest.fixture(scope='session')
def csv_file():
    path = os.path.dirname(os.path.realpath(__file__))
    csv_file_path = os.path.join(path, 'data', 'test-brownfield-register.csv')
    return csv_file_path


@pytest.fixture(scope='session')
def schema_file():
    path = Path(os.path.dirname(os.path.realpath(__file__))).parent
    schema_file_path = os.path.join(path, 'application', 'validation', 'schema', 'brownfield-land-v2.json')
    return schema_file_path


def test_check_original_data_in_end_to_end_validation(csv_file, schema_file, original_data):

    report = validate_file(csv_file, schema_file)

    assert report.raw_result['tables'][0]['error-count'] == 7
    assert len(report.original_data) == 2
    assert len(report.original_data) == len(original_data)
    assert set(report.original_data[0].keys()) == set(original_data[0].keys())
    assert set(report.original_data[1].keys()) == set(original_data[1].keys())
    assert set(report.original_data[0].values()) == set(original_data[0].values())
    assert set(report.original_data[1].values()) == set(original_data[1].values())


def test_check_validated_data_in_end_to_end_validation(csv_file, schema_file, validated_data):

    report = validate_file(csv_file, schema_file)

    assert report.raw_result['tables'][0]['error-count'] == 7
    assert len(report.validated_data) == 2
    assert len(report.validated_data) == len(validated_data)
    assert set(report.validated_data[0].keys()) == set(validated_data[0].keys())
    assert set(report.validated_data[1].keys()) == set(validated_data[1].keys())
    assert set(report.validated_data[0].values()) == set(validated_data[0].values())
    assert set(report.validated_data[1].values()) == set(validated_data[1].values())


def test_check_errors_by_column_in_end_to_end_validation(csv_file, schema_file):

    report = validate_file(csv_file, schema_file)

    assert len(report.errors_by_column['GeoX']['errors']) == 2
    assert len(report.errors_by_column['GeoY']['errors']) == 2
    assert len(report.errors_by_column['SiteplanURL']['errors']) == 1
    assert len(report.errors_by_column['PlanningHistory']['errors']) == 1

    assert report.errors_by_column['GeoX']['rows'] == [1,2]
    assert report.errors_by_column['GeoY']['rows'] == [1,2]
    assert report.errors_by_column['SiteplanURL']['rows'] == [1]
    assert report.errors_by_column['PlanningHistory']['rows'] == [1]


def test_check_errors_by_row_in_end_to_end_validation(csv_file, schema_file):

    report = validate_file(csv_file, schema_file)

    assert len(report.errors_by_row) == 2

    assert report.errors_by_row[0]['GeoX']['row'] == 1
    assert report.errors_by_row[0]['GeoX']['error'] is not None

    assert report.errors_by_row[1]['GeoX']['row'] == 2
    assert report.errors_by_row[1]['GeoX']['error'] is not None

    assert report.errors_by_row[0]['GeoY']['row'] == 1
    assert report.errors_by_row[0]['GeoY']['error'] is not None

    assert report.errors_by_row[1]['GeoY']['row'] == 2
    assert report.errors_by_row[1]['GeoY']['error'] is not None

    assert report.errors_by_row[0]['SiteplanURL']['row'] == 1
    assert report.errors_by_row[0]['SiteplanURL']['error'] is not None

    assert report.errors_by_row[1]['SiteplanURL']['row'] == 2
    assert report.errors_by_row[1]['SiteplanURL']['error'] is None

    assert report.errors_by_row[0]['PlanningHistory']['row'] == 1
    assert report.errors_by_row[0]['PlanningHistory']['error'] is not None

    assert report.errors_by_row[1]['PlanningHistory']['row'] == 2
    assert report.errors_by_row[1]['PlanningHistory']['error'] is None