import logging
import goodtables

from goodtables import check
from application.validation.utils import extract_data, FileTypeException
from application.validation.reporter import Report
from application.validation.schema import brownfield_site_schema

custom_checks=['geox-check','geoy-check']
builtin_checks = ['structure', 'schema']
checks = builtin_checks + custom_checks


def handle_upload_and_validate(data, filename):
    try:
        extracted_data = extract_data(data, filename)
        result = check(extracted_data['rows_to_check'])
        checked_rows = extracted_data.pop('rows_to_check', None)
        original_rows = extracted_data.pop('original_rows', None)
        return Report(raw_result=result,
                      checked_rows=checked_rows,
                      original_rows=original_rows,
                      additional_data=extracted_data)
    except FileTypeException as e:
        logging.exception(e)
        raise e


def check(data):
    return goodtables.validate(data, schema=brownfield_site_schema, order_fields=True, checks=checks)
