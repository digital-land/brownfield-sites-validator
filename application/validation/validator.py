import goodtables

from application.utils import extract_and_normalise_data
from application.validation.reporter import Report
from application.validation.schema import brownfield_site_schema


def handle_upload_and_validate(form):
    data, additional_fields, file_type = extract_and_normalise_data(form.upload.data)
    results = check(data)
    return Report(results, data=data, additional=additional_fields, file_type=file_type)


def check(data):
    return goodtables.validate(data, schema=brownfield_site_schema, order_fields=True)
