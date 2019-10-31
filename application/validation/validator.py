import goodtables
from bidict import bidict

from application.utils import extract_and_normalise_data, updated_brownfield_register_fields
from application.validation.schema import brownfield_site_schema


def handle_upload_and_validate(form):
    data, additional_fields = extract_and_normalise_data(form.upload.data)
    return check(data, additional_fields)


def check(data, additional_fields):
    # TODO extract results and make report
    results = goodtables.validate(data, schema=brownfield_site_schema, order_fields=True)
    results['additional-fields'] = additional_fields  # make this part of report not results
    return results


class Report:

    def __init__(self, results, data):
        self.results = results
        self.data = data
        cols_to_fields = {}
        for column_number, header in enumerate(self.results['tables'][0]['headers']):
            cols_to_fields[column_number + 1] = header
        self.columns_to_fields = bidict(cols_to_fields)

    def error_count(self):
        return self.results['error-count']

    def errors_by_field(self, field):
        column_number = self.field_name_to_column_number(field)
        errors = {'field': field}
        for error in self.results['tables'][0]['errors']:
            if error['column-number'] == column_number:
                if errors.get(error['code']) is None:
                    errors[error['code']] = {'count': 1, 'message-data': error['message-data']}
                else:
                    errors[error['code']]['count'] += 1
        return errors

    def column_number_to_field_name(self, index):
        try:
            return self.columns_to_fields[index]
        except KeyError as e:
            return 'unknown'

    def field_name_to_column_number(self, field):
        try:
            return self.columns_to_fields.inverse[field]
        except KeyError as e:
            return -1

