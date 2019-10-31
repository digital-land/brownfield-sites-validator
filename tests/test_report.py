import os

import pytest
import json

from application.validation.validator import Report


@pytest.fixture(scope='session')
def results():
    path = os.path.dirname(os.path.realpath(__file__))
    data_file_path = os.path.join(path, 'data', 'results.json')
    with open(data_file_path, 'r') as f:
        data = json.load(f)
    return data


def test_report_shows_total_number_of_errors(results):
    report = Report(results, {})
    assert 102 == report.error_count()


def test_column_number_to_field_name(results):
    report = Report(results, {})
    assert report.column_number_to_field_name(1) == 'Deliverable'
    assert report.column_number_to_field_name(2) == 'FirstAddedDate'
    assert report.column_number_to_field_name(3) == 'GeoX'
    assert report.column_number_to_field_name(4) == 'GeoY'
    assert report.column_number_to_field_name(5) == 'HazardousSubstances'
    assert report.column_number_to_field_name(6) == 'Hectares'
    assert report.column_number_to_field_name(7) == 'LastUpdatedDate'
    assert report.column_number_to_field_name(8) == 'NetDwellingsRangeFrom'
    assert report.column_number_to_field_name(9) == 'NetDwellingsRangeTo'
    assert report.column_number_to_field_name(10) == 'Notes'
    assert report.column_number_to_field_name(11) == 'OrganisationURI'
    assert report.column_number_to_field_name(12) == 'OwnershipStatus'
    assert report.column_number_to_field_name(13) == 'PermissionDate'
    assert report.column_number_to_field_name(14) == 'PermissionType'
    assert report.column_number_to_field_name(15) == 'PlanningHistory'
    assert report.column_number_to_field_name(16) == 'PlanningStatus'
    assert report.column_number_to_field_name(17) == 'SiteNameAddress'
    assert report.column_number_to_field_name(18) == 'SiteReference'

    assert report.column_number_to_field_name(19) == 'SiteplanURL'

    assert report.column_number_to_field_name(0) == 'unknown'
    assert report.column_number_to_field_name(20) == 'unknown'


def test_field_name_to_column_number(results):
    report = Report(results, {})
    assert 1 == report.field_name_to_column_number('Deliverable')
    assert 2 == report.field_name_to_column_number("FirstAddedDate")
    assert 3 == report.field_name_to_column_number('GeoX')
    assert 4 == report.field_name_to_column_number('GeoY')
    assert 5 == report.field_name_to_column_number('HazardousSubstances')
    assert 6 == report.field_name_to_column_number('Hectares')
    assert 7 == report.field_name_to_column_number('LastUpdatedDate')
    assert 8 == report.field_name_to_column_number('NetDwellingsRangeFrom')
    assert 9 == report.field_name_to_column_number('NetDwellingsRangeTo')
    assert 10 == report.field_name_to_column_number('Notes')
    assert 11 == report.field_name_to_column_number('OrganisationURI')
    assert 12 == report.field_name_to_column_number('OwnershipStatus')
    assert 13 == report.field_name_to_column_number('PermissionDate')
    assert 14 == report.field_name_to_column_number('PermissionType')
    assert 15 == report.field_name_to_column_number('PlanningHistory')
    assert 16 == report.field_name_to_column_number('PlanningStatus')
    assert 17 == report.field_name_to_column_number('SiteNameAddress')
    assert 18 == report.field_name_to_column_number('SiteReference')

    assert 19 == report.field_name_to_column_number('SiteplanURL')

    assert -1 == report.field_name_to_column_number('unknown')


def test_report_shows_error_counts_by_first_added_date(results):

    report = Report(results, {})
    expected ={'field': 'FirstAddedDate',
               'type-or-format-error': {'count': 27,
                                        'message-data': {'value': '26/02/2018',
                                                         'field_type': 'date',
                                                         'field_format': 'default'}}}

    assert expected == report.errors_by_field('FirstAddedDate')


def test_report_shows_error_counts_by_deliverable(results):

    report = Report(results, {})
    expected ={'field': 'Deliverable',
               'pattern-constraint': {'count': 27,
                                      'message-data': {'constraint': 'Y',
                                                       'value': 'Yes'}}}

    assert expected == report.errors_by_field('Deliverable')
