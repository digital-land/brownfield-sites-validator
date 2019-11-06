import logging
import goodtables

from goodtables import check
from application.validation.utils import extract_data
from application.validation.reporter import Report
from application.validation.schema import brownfield_site_schema

custom_checks=['geox-check','geoy-check']
builtin_checks = ['structure', 'schema']
checks = builtin_checks + custom_checks


def handle_upload_and_validate(data, filename):
    try:
        extracted_data = extract_data(data, filename)
        results = check(extracted_data['data'])
        return Report(results, extracted_data)
    except Exception as e:
        logging.exception(e)
        raise e


def check(data):
    return goodtables.validate(data, schema=brownfield_site_schema, order_fields=True, checks=checks)
