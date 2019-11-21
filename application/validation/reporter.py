from bidict import bidict

from application.validation.error_mapper import ErrorMapper
from application.validation.utils import BrownfieldStandard


class Report:

    def __init__(self,
                 raw_result,
                 original_data,
                 validated_data,
                 additional_data,
                 errors_by_row=None,
                 errors_by_column=None,
                 id=None):

        self.id = id
        self.raw_result = raw_result
        self.original_data = original_data
        self.validated_data = validated_data
        self.additional_data = additional_data
        cols_to_headers = {}
        for column_number, header in enumerate(self.raw_result['tables'][0]['headers']):
            cols_to_headers[column_number + 1] = header
        self.column_numbers_to_headers = bidict(cols_to_headers)
        if errors_by_row is None:
            self.errors_by_row = self.collect_row_errors()
        else:
            self.errors_by_row = errors_by_row
        if errors_by_column is None:
            self.errors_by_column = self.collect_column_errors()
        else:
            self.errors_by_column = errors_by_column

    def valid(self):
        return self.raw_result['valid']

    def row_count(self):
        return self.raw_result['tables'][0]['row-count']

    def headers_found(self):
        return self.additional_data.get('headers_found', [])

    def correct_headers_found(self):
        return list(set(self.headers_found()) - set(self.additional_headers()))

    def extra_headers_found(self):
        return list(set(self.additional_headers()) - set(BrownfieldStandard.headers_deprecated()))

    def deprecated_headers_found(self):
        return list(set(self.additional_headers()) - set(self.extra_headers_found()))

    def additional_headers(self):
        return self.additional_data.get('additional_headers', [])

    def headers_missing(self):
        return self.additional_data.get('headers_missing', [])

    def file_type(self):
        return self.additional_data.get('file_type')

    def planning_authority(self):
        return self.additional_data.get('planning_authority')

    def error_count(self):
        return self.raw_result['error-count']

    def check_headers(self):
        report_headers = self.headers_found()
        headers_status = "Headers correct"
        for header in BrownfieldStandard.v2_standard_headers():
            if header not in report_headers:
                headers_status = "Missing headers"
        for header in BrownfieldStandard.headers_deprecated():
            if header in report_headers:
                headers_status = "Warnings"
        if len(self.additional_headers()) > 0:
            headers_status = "Extra headers"
        return headers_status

    def column_number_to_header(self, index):
        try:
            return self.column_numbers_to_headers[index]
        except KeyError as e: # noqa
            return 'unknown'

    def header_to_column_number(self, header):
        try:
            return self.column_numbers_to_headers.inverse[header]
        except KeyError as e: # noqa
            return -1

    def collect_column_errors(self):
        errs = {}
        for column in BrownfieldStandard.v2_standard_headers():
            errs = {**errs, **self.collect_errors_by_column(column)}
        return errs

    def collect_errors_by_column(self, column):
        column_number = self.header_to_column_number(column)
        messages = set([])
        errs = []
        rows = []
        errors = {}
        for e in self.raw_result['tables'][0]['errors']:
            mapper = ErrorMapper.factory(e, column)
            if e.get('column-number') is not None and e.get('column-number') == column_number:
                if 'row-number' in e.keys():
                    rows.append(e['row-number'])
                messages.add(mapper.overall_error_messages())
                value = e.get('message-data').get('value') if e.get('message-data') else None
                err = {'message': mapper.field_error_message(),
                       'row': e.get('row-number', 0),
                       'fix': mapper.get_fix_if_possible(),
                       'value': value
                       }
                errs.append(err)
        if errs:
            errors[column] = {'rows': rows,
                              'errors': errs,
                              'messages': list(messages)}
        return errors

    def collect_row_errors(self):
        rows = []
        for row_number, data_row in enumerate(self.validated_data):
            row = {}
            for header, value in data_row.items():
                error = self.collect_errors_by_row(header, row_number + 1)
                row[header] = {'value': value, 'error': error, 'row': row_number + 1}
            rows.append(row)
        return rows

    def collect_errors_by_row(self, header, row_number):
        error = None
        column_number = self.header_to_column_number(header)
        for e in self.raw_result['tables'][0]['errors']:
            mapper = ErrorMapper.factory(e, header)
            if e.get('column-number') is not None and e.get('column-number') == column_number \
                    and e.get('row-number') == row_number:
                error = {'message': mapper.field_error_message(), 'fix': mapper.get_fix_if_possible()}
        return error

    def valid_row_count(self):
        return self.row_count() - len(self.invalid_rows())

    def invalid_rows(self):
        rows = []
        for error in self.raw_result['tables'][0]['errors']:
            if 'row-number' in error.keys():
                rows.append(error['row-number'])
        return set(rows)

    def to_dict(self):
        return {
            'id': str(self.id),
            'headers_expected': BrownfieldStandard.v2_standard_headers(),
            'headers_found': self.headers_found(),
            'headers_missing': self.headers_missing(),
            'additional_headers': self.additional_headers(),
            'original_data': self.original_data,
            'validated_data': self.validated_data,
            'errors_by_row': self.errors_by_row,
            'errors_by_column': self.errors_by_column
        }
