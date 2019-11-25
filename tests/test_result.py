# flake8: noqa

import json
import os
import pytest

from datetime import datetime
from application.validation.validation_result import Result


@pytest.fixture(scope='session')
def result():
    path = os.path.dirname(os.path.realpath(__file__))
    data_file_path = os.path.join(path, 'data', 'result.json')
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
    from tests.data.test_data import upload
    return upload


@pytest.fixture(scope='session')
def validated_data():
    from tests.data.test_data import rows
    return rows


@pytest.fixture(scope='session')
def additional_data():
    from tests.data.test_data import meta_data
    return meta_data


def test_result_shows_total_number_of_errors(result, original_data, rows, meta_data):
    result = Result(result=result,
                    upload=original_data,
                    rows=rows,
                    meta_data=meta_data)
    assert 7 == result.error_count()


def test_column_number_to_field_name(result, original_data, rows, meta_data):

    result = Result(result=result,
                    upload=original_data,
                    rows=rows,
                    meta_data=meta_data)

    assert result.column_number_to_header(1) == 'Deliverable'
    assert result.column_number_to_header(2) == 'FirstAddedDate'
    assert result.column_number_to_header(3) == 'GeoX'
    assert result.column_number_to_header(4) == 'GeoY'
    assert result.column_number_to_header(5) == 'HazardousSubstances'
    assert result.column_number_to_header(6) == 'Hectares'
    assert result.column_number_to_header(7) == 'LastUpdatedDate'
    assert result.column_number_to_header(8) == 'NetDwellingsRangeFrom'
    assert result.column_number_to_header(9) == 'NetDwellingsRangeTo'
    assert result.column_number_to_header(10) == 'Notes'
    assert result.column_number_to_header(11) == 'OrganisationURI'
    assert result.column_number_to_header(12) == 'OwnershipStatus'
    assert result.column_number_to_header(13) == 'PermissionDate'
    assert result.column_number_to_header(14) == 'PermissionType'
    assert result.column_number_to_header(15) == 'PlanningHistory'
    assert result.column_number_to_header(16) == 'PlanningStatus'
    assert result.column_number_to_header(17) == 'SiteNameAddress'
    assert result.column_number_to_header(18) == 'SiteReference'
    assert result.column_number_to_header(19) == 'SiteplanURL'
    assert result.column_number_to_header(0) == 'unknown'
    assert result.column_number_to_header(20) == 'unknown'


def test_field_name_to_column_number(result, original_data, rows, meta_data):

    result = Result(result=result,
                    upload=original_data,
                    rows=rows,
                    meta_data=meta_data)

    assert 1 == result.header_to_column_number('Deliverable')
    assert 2 == result.header_to_column_number("FirstAddedDate")
    assert 3 == result.header_to_column_number('GeoX')
    assert 4 == result.header_to_column_number('GeoY')
    assert 5 == result.header_to_column_number('HazardousSubstances')
    assert 6 == result.header_to_column_number('Hectares')
    assert 7 == result.header_to_column_number('LastUpdatedDate')
    assert 8 == result.header_to_column_number('NetDwellingsRangeFrom')
    assert 9 == result.header_to_column_number('NetDwellingsRangeTo')
    assert 10 == result.header_to_column_number('Notes')
    assert 11 == result.header_to_column_number('OrganisationURI')
    assert 12 == result.header_to_column_number('OwnershipStatus')
    assert 13 == result.header_to_column_number('PermissionDate')
    assert 14 == result.header_to_column_number('PermissionType')
    assert 15 == result.header_to_column_number('PlanningHistory')
    assert 16 == result.header_to_column_number('PlanningStatus')
    assert 17 == result.header_to_column_number('SiteNameAddress')
    assert 18 == result.header_to_column_number('SiteReference')
    assert 19 == result.header_to_column_number('SiteplanURL')
    assert -1 == result.header_to_column_number('unknown')


def test_result_shows_error_counts_by_column(result, original_data, rows, meta_data):

    result = Result(result=result,
                    upload=original_data,
                    rows=rows,
                    meta_data=meta_data)

    expected = {'PlanningHistory': {'errors': [
                                    {'fix': None,
                                     'message': 'notaurl is not a url',
                                     'row': 1,
                                     'value': 'https://planningapps.winchester.gov.uk/online-applications/search.do?action=simple&searchType=Application|notaurl'}],
                'messages': ['This column can contain one or more URLs separated by a pipe (‘|’) character'],
                'rows': [1]}}
    assert expected == result.collect_errors_by_column('PlanningHistory')
