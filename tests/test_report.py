import json
import os
from datetime import datetime

import pytest

from application.validation.reporter import Report


@pytest.fixture(scope='session')
def results():
    path = os.path.dirname(os.path.realpath(__file__))
    data_file_path = os.path.join(path, 'data', 'results.json')
    with open(data_file_path, 'r') as f:
        data = json.load(f)
    return data


@pytest.fixture(scope='session')
def date_error_message():
    today = datetime.today()
    today_human = today.strftime('%d/%m/%Y')
    today_iso = today.strftime('%Y-%m-%d')
    return f'Some dates in the file are not in the format YYYY-MM-DD. For example {today_human} should be {today_iso}'


def test_report_shows_total_number_of_errors(results):
    report = Report(raw_result=results)
    assert 7 == report.error_count()


def test_column_number_to_field_name(results):
    report = Report(raw_result=results)
    assert report.column_number_to_header(1) == 'Deliverable'
    assert report.column_number_to_header(2) == 'FirstAddedDate'
    assert report.column_number_to_header(3) == 'GeoX'
    assert report.column_number_to_header(4) == 'GeoY'
    assert report.column_number_to_header(5) == 'HazardousSubstances'
    assert report.column_number_to_header(6) == 'Hectares'
    assert report.column_number_to_header(7) == 'LastUpdatedDate'
    assert report.column_number_to_header(8) == 'NetDwellingsRangeFrom'
    assert report.column_number_to_header(9) == 'NetDwellingsRangeTo'
    assert report.column_number_to_header(10) == 'Notes'
    assert report.column_number_to_header(11) == 'OrganisationURI'
    assert report.column_number_to_header(12) == 'OwnershipStatus'
    assert report.column_number_to_header(13) == 'PermissionDate'
    assert report.column_number_to_header(14) == 'PermissionType'
    assert report.column_number_to_header(15) == 'PlanningHistory'
    assert report.column_number_to_header(16) == 'PlanningStatus'
    assert report.column_number_to_header(17) == 'SiteNameAddress'
    assert report.column_number_to_header(18) == 'SiteReference'
    # TODO change this when column name fixup is done
    assert report.column_number_to_header(19) == 'SiteplanURL'
    assert report.column_number_to_header(0) == 'unknown'
    assert report.column_number_to_header(20) == 'unknown'


def test_field_name_to_column_number(results):
    report = Report(raw_result=results)
    assert 1 == report.header_to_column_number('Deliverable')
    assert 2 == report.header_to_column_number("FirstAddedDate")
    assert 3 == report.header_to_column_number('GeoX')
    assert 4 == report.header_to_column_number('GeoY')
    assert 5 == report.header_to_column_number('HazardousSubstances')
    assert 6 == report.header_to_column_number('Hectares')
    assert 7 == report.header_to_column_number('LastUpdatedDate')
    assert 8 == report.header_to_column_number('NetDwellingsRangeFrom')
    assert 9 == report.header_to_column_number('NetDwellingsRangeTo')
    assert 10 == report.header_to_column_number('Notes')
    assert 11 == report.header_to_column_number('OrganisationURI')
    assert 12 == report.header_to_column_number('OwnershipStatus')
    assert 13 == report.header_to_column_number('PermissionDate')
    assert 14 == report.header_to_column_number('PermissionType')
    assert 15 == report.header_to_column_number('PlanningHistory')
    assert 16 == report.header_to_column_number('PlanningStatus')
    assert 17 == report.header_to_column_number('SiteNameAddress')
    assert 18 == report.header_to_column_number('SiteReference')
    # TODO change this when column name fixup is done
    assert 19 == report.header_to_column_number('SiteplanURL')
    assert -1 == report.header_to_column_number('unknown')


def test_report_shows_error_counts_by_first_added_date(results, date_error_message):
    report = Report(raw_result=results)
    today = datetime.today()
    today_string = today.strftime('%d/%m/%Y')
    today_iso = today.strftime('%Y-%m-%d')
    expected = {'column': 'FirstAddedDate',
                'errors': [{'fix': '2018-03-18',
                            'message': 'The date 18/03/2018 should be entered as 2018-03-18',
                            'row': 3,
                            'value': '18/03/2018'},
                           {'fix': '2018-02-26',
                            'message': 'The date 26/02/2018 should be entered as 2018-02-26',
                            'row': 8,
                            'value': '26/02/2018'}],
                'messages': [f'Some dates in the file are not in the format YYYY-MM-DD. For example {today_string} should be {today_iso}'],
                'rows': [3, 8]}
    assert expected == report.collect_errors_by_column('FirstAddedDate')
