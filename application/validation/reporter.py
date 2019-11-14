import uuid
from datetime import datetime

from bidict import bidict
from sqlalchemy.dialects.postgresql import UUID, JSONB

from application.extensions import db
from application.validation.error_mapper import ErrorMapper
from application.validation.utils import BrownfieldStandard


class Report(db.Model):

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_result = db.Column(JSONB, default=dict)
    original_rows = db.Column(JSONB, default=dict)
    checked_rows = db.Column(JSONB, default=dict)
    additional_data = db.Column(JSONB, default=dict)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super(Report, self).__init__(**kwargs)
        self.attach_errors_to_rows()

    def valid(self):
        return self.raw_result['valid']

    def row_count(self):
        return self.raw_result['tables'][0]['row-count']

    def headers_found(self):
        return self.additional_data.get('headers_found', [])

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

    def column_numbers_to_headers(self):
        cols_to_headers = {}
        for column_number, header in enumerate(self.raw_result['tables'][0]['headers']):
            cols_to_headers[column_number + 1] = header
        return bidict(cols_to_headers)

    def column_number_to_header(self, index):
        try:
            return self.column_numbers_to_headers()[index]
        except KeyError as e:
            return 'unknown'

    def header_to_column_number(self, header):
        try:
            return self.column_numbers_to_headers().inverse[header]
        except KeyError as e:
            return -1

    def collect_errors_by_column(self, column):
        column_number = self.header_to_column_number(column)
        errors = {'column': column, 'errors': [], 'rows': []}
        messages = set([])
        for e in self.raw_result['tables'][0]['errors']:
            mapper = ErrorMapper.factory(e, column)
            if e.get('column-number') is not None and e.get('column-number') == column_number:
                if 'row-number' in e.keys():
                    errors['rows'].append(e['row-number'])
                messages.add(mapper.overall_error_messages())
                value = e.get('message-data').get('value') if e.get('message-data') else None
                err = {'message': mapper.field_error_message(),
                       'row': e.get('row-number', 0),
                       'fix': mapper.get_fix_if_possible(),
                       'value': value
                       }
                errors['errors'].append(err)
        errors['rows'] = list(dict.fromkeys(errors['rows']))
        errors['messages'] = list(messages)
        return errors

    def errors_by_columns(self):
        errs = []
        for column in BrownfieldStandard.v2_standard_headers():
            e = self.collect_errors_by_column(column)
            if e['errors']:
                errs.append(e)
        return errs

    def collect_errors_by_row(self, header, row_number):
        error = {}
        column_number = self.header_to_column_number(header)
        for e in self.raw_result['tables'][0]['errors']:
            mapper = ErrorMapper.factory(e, header)
            if e.get('column-number') is not None and e.get('column-number') == column_number and e.get('row-number') == row_number:
                error['message'] = mapper.field_error_message()
                error['fix'] = mapper.get_fix_if_possible()
        return error

    def attach_errors_to_rows(self):
        rows = []
        if self.checked_rows:
            for row_number, data_row in enumerate(self.checked_rows):
                row = {}
                for header, value in data_row.items():
                    error = self.collect_errors_by_row(header, row_number + 1)
                    row[header] = {'value': value, 'error': error, 'row': row_number + 1}
                rows.append(row)
        self.checked_rows = rows

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
            'checked_rows': self.checked_rows,
            'original_rows': self.original_rows,
            'errors_by_column': self.errors_by_columns()
        }
