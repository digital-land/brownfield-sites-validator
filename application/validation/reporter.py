import json

from bidict import bidict

from application.validation.error_mapper import ErrorMapper


class Report:

    def __init__(self, results, data):
        self.results = results
        self.data = data['data']
        self.additional = data.get('additional_fields', [])
        self.file_type =  data.get('file_type', 'csv')
        self.planning_authority =  data.get('planning_authority', 'Not known')
        cols_to_fields = {}
        for column_number, header in enumerate(self.results['tables'][0]['headers']):
            cols_to_fields[column_number + 1] = header
        self.columns_to_fields = bidict(cols_to_fields)

    def valid(self):
        return self.results['valid']

    def row_count(self):
        return self.results['tables'][0]['row-count']

    def headers(self):
        return self.results['tables'][0]['headers']

    def additional_fields(self):
        return self.additional

    def error_count(self):
        return self.results['error-count']

    # TODO map error types to better names and work out what to extract from messages and values
    def errors_by_field(self, field):
        column_number = self.field_name_to_column_number(field)
        errors = {'field': field, 'errors': [], 'rows': []}
        for e in self.results['tables'][0]['errors']:
            mapper = ErrorMapper(e)
            if e['column-number'] == column_number:
                if 'row-number' in e.keys():
                    errors['rows'].append(e['row-number'])
                if errors.get('message') is None:
                    errors['message'] = mapper.overall_error_message()
                err = {'type': e['code'], 'message': mapper.field_error_message(), 'row': e.get('row-number', 0)}
                errors['errors'].append(err)
        errors['rows'] = list(dict.fromkeys(errors['rows']))
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

    def errors(self):
        errs = []
        for field in self.headers():
            e = self.errors_by_field(field)
            if e['errors']:
                errs.append(e)
        return errs

    def raw_data(self):
        return json.dumps(self.results,
                          sort_keys=False,
                          indent=2)

    def valid_row_count(self):
        return self.row_count() - len(self.invalid_rows())

    def invalid_rows(self):
        rows = []
        for error in self.results['tables'][0]['errors']:
            if 'row-number' in error.keys():
                rows.append(error['row-number'])
        return set(rows)