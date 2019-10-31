import goodtables

from application.utils import extract_and_normalise_data
from application.validation.schema import brownfield_site_schema


def handle_upload_and_validate(form):
    data, additional_fields = extract_and_normalise_data(form.upload.data)
    return check(data, additional_fields)


def check(data, additional_fields):
    # TODO extract results and make report
    results = goodtables.validate(data, schema=brownfield_site_schema, order_fields=True)
    results['additional-fields'] = additional_fields  # make this part of report not results
    return results