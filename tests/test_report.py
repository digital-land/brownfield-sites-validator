import json
import os
import pytest

from datetime import datetime

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


@pytest.fixture(scope='session')
def original_data():
    from tests.data.test_data import original_data
    return original_data


@pytest.fixture(scope='session')
def validated_data():
    from tests.data.test_data import validated_data
    return validated_data


@pytest.fixture(scope='session')
def additional_data():
    from tests.data.test_data import additional_data
    return additional_data


def test_report_shows_total_number_of_errors(results, original_data, validated_data, additional_data):
    report = Report(raw_result=results,
                    original_data=original_data,
                    validated_data=validated_data,
                    additional_data = additional_data)
    assert 7 == report.error_count()


def test_column_number_to_field_name(results, original_data, validated_data, additional_data):

    report = Report(raw_result=results,
                    original_data=original_data,
                    validated_data=validated_data,
                    additional_data = additional_data)

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
    assert report.column_number_to_header(19) == 'SiteplanURL'
    assert report.column_number_to_header(0) == 'unknown'
    assert report.column_number_to_header(20) == 'unknown'


def test_field_name_to_column_number(results, original_data, validated_data, additional_data):

    report = Report(raw_result=results,
                    original_data=original_data,
                    validated_data=validated_data,
                    additional_data = additional_data)

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
    assert 19 == report.header_to_column_number('SiteplanURL')
    assert -1 == report.header_to_column_number('unknown')


def test_report_shows_error_counts_by_column(results, original_data, validated_data, additional_data):

    report = Report(raw_result=results,
                    original_data=original_data,
                    validated_data=validated_data,
                    additional_data = additional_data)

    expected = {'PlanningHistory': {'errors': [{'fix': None,
                                 'message': 'notaurl is not a url',
                                 'row': 1,
                                 'value': 'https://planningapps.winchester.gov.uk/online-applications/search.do?action=simple&searchType=Application|notaurl'}],
                     'messages': ['This column can contain one or more URLs '
                                  'separated by a pipe (‘|’) character'],
                     'rows': [1]}}
    assert expected == report.collect_errors_by_column('PlanningHistory')
