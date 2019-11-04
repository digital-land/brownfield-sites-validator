import datetime

import pytest

from application.validation.error_mapper import ErrorMapper


@pytest.fixture(scope='session')
def date_error():
    return {
          "code": "type-or-format-error",
          "row-number": 1,
          "column-number": 2,
          "message": "The value \"26/02/2018\" in row 1 and column 2 is not type \"date\" and format \"default\"",
          "message-data": {
            "value": "26/02/2018",
            "field_type": "date",
            "field_format": "default"
          }
        }


def test_error_mapper_returns_overall_error_message(date_error):
    today = datetime.datetime.today()
    today_human = today.strftime('%d/%m/%Y')
    today_iso = today.strftime('%Y-%m-%d')
    expected = f'Some dates in the file are not in the format YYYY-MM-DD. For example {today_human} should be {today_iso}'

    error_mapper = ErrorMapper(date_error, 'some-field')
    assert error_mapper.overall_error_messages() == expected


def test_error_mapper_returns_specfic_error_message_for_field(date_error):
    error_mapper = ErrorMapper(date_error, 'some-field')
    assert error_mapper.field_error_message() == 'The date 26/02/2018 should be entered as 2018-02-26'
