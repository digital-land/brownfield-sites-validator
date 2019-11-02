import goodtables
from goodtables import check, Error
from goodtables.config import CHECKS

from application.utils import extract_and_normalise_data
from application.validation.reporter import Report
from application.validation.schema import brownfield_site_schema

custom_checks=['geox-check','geoy-check']
builtin_checks = ['structure', 'schema']
checks = builtin_checks + custom_checks


def handle_upload_and_validate(form):
    extracted_data = extract_and_normalise_data(form.upload.data)
    results = check(extracted_data['data'])
    return Report(results, extracted_data)


def check(data):
    return goodtables.validate(data, schema=brownfield_site_schema, order_fields=True, checks=checks)
