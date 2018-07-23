import csv

from io import StringIO
from collections import defaultdict

import requests

from enum import Enum

from requests.exceptions import InvalidSchema, HTTPError, MissingSchema


class Error(Enum):
    INVALID_URL = 'An invalid URL was found in the file'
    INVALID_DATE = 'Date format should be YYYY-MM-DD'
    NO_LINE_BREAK = 'No line breaks allowed'
    REQUIRED_FIELD = 'Required data is missing'
    INVALID_FLOAT = 'This field must contain a floating point number'
    INVALID_CSV_HEADERS = 'This file does not contain the expected headers'


class Warning(Enum):
    HTTP_WARNING = 'There was a problem fetching data from a URL in the file'
    DATE_WARNING = 'The date is in the future. Please check'
    CONTENT_TYPE_WARNING = 'Set Content-Type to test/csv;charset-utf8'
    FILE_ENCODING_WARNING = 'File should be encoded as utf-8'


class StringInput():

    ''' Read a file from a string '''

    def __init__(self, string_input=None, string_io=None):
        self.string_io = string_io if string_io else StringIO(string_input)

    def open(self):
        return self.string_io


class ValidationIssue:

    def __init__(self, data, type_, message = None):
        self.data = data
        self.type_ = type_
        self.message = message


class BaseFieldValidator:

    def __init__(self, allow_empty=False):
        self.allow_empty = allow_empty

    def validate(self, field, row):
        raise NotImplementedError


class URLValidator(BaseFieldValidator):

    ''' Field must be a valid url and reachable '''

    def __init__(self, **kwargs):
        super(URLValidator, self).__init__(**kwargs)
        self.checked = set([])

    def validate(self, data, row={}):
        errors = []
        warnings = []
        if (data or not self.allow_empty) and data not in self.checked:
            try:
                resp = requests.get(data)
                resp.raise_for_status()
                self.checked.add(data)
            except (InvalidSchema, MissingSchema) as e:
                errors.append(ValidationIssue(data, Error.INVALID_URL, message=e))
            except HTTPError as e:
                warnings.append(ValidationIssue(data, Warning.HTTP_WARNING, message=e))

        return errors, warnings


class StringNoLineBreaksValidator(BaseFieldValidator):

    ''' Field cannot contain line breaks '''

    def __init__(self, **kwargs):
        super(StringNoLineBreaksValidator, self).__init__(**kwargs)

    def validate(self, data, row={}):
        errors = []
        warnings = []
        if (data or not self.allow_empty) and ('\r\n' in data or '\n' in data):
            errors.append(ValidationIssue(data, Error.NO_LINE_BREAK))
        return errors, warnings


class ISO8601DateValidator(BaseFieldValidator):

    ''' Field must be iso-8601 formatted date string '''

    def __init__(self, **kwargs):
        super(ISO8601DateValidator, self).__init__(**kwargs)

    def validate(self, data, row={}):
        import datetime
        errors = []
        warnings = []
        if data or not self.allow_empty:
            try:
                datetime.datetime.strptime(data, '%Y-%m-%d')
            except ValueError as e:
                errors.append(ValidationIssue(data, Error.INVALID_DATE))

        return errors, warnings


class NotEmptyValidator(BaseFieldValidator):

    ''' Field cannot be empty '''

    def __init__(self, **kwargs):
        super(NotEmptyValidator, self).__init__(**kwargs)

    def validate(self, data, row={}):
        errors = []
        warnings = []
        if data.strip() == '':
            errors.append(ValidationIssue(data, Error.REQUIRED_FIELD))
        return errors, warnings


class FloatValidator(BaseFieldValidator):

    def __init__(self, **kwargs):
        super(FloatValidator, self).__init__(**kwargs)

    def validate(self, data, row={}):
        errors = []
        warnings = []
        try:
            if data or not self.allow_empty:
                float(data)
        except ValueError as e:
            errors.append(ValidationIssue(data, Error.INVALID_FLOAT))
        return errors, warnings


class AnythingValidator(BaseFieldValidator):
    ''' Field needs to be present but can be pretty much any content '''

    def validate(self, field, row={}):
        pass


class CrossFieldValidator(BaseFieldValidator):

    ''' Checks field against another field in row '''

    def __init__(self, validate_against_fields=[], **kwargs):
        super(CrossFieldValidator, self).__init__(**kwargs)
        self.validate_against_fields = validate_against_fields

    def validate(self, field, row):
        pass


class RegisterValidator:

    def __init__(self, source, file_warnings, line_count, validators={}, delimiter=None):

        self.source = source
        self.file_warnings = file_warnings
        self.file_errors = []
        self.line_count = line_count
        self.errors = defaultdict(lambda: defaultdict(list))
        self.warnings = defaultdict(lambda: defaultdict(list))
        self.missing = []
        self.unknown = []
        self.validators = validators or getattr(self, 'validators', {})
        self.delimiter = delimiter or getattr(self, 'delimiter', ',')
        self.rows_analysed = 0
        self.report = {}

    def validate(self):

        reader = csv.DictReader(self.source.open(), delimiter=self.delimiter)
        self.missing = set(self.validators) - set(reader.fieldnames)

        # if this happens, then file headers are completely broken and not point
        # carrying on
        if self.missing == set(self.validators):
            self.file_errors = ValidationIssue('file', Error.INVALID_CSV_HEADERS)
            self.unknown = set(reader.fieldnames)
            return self

        for line, row in enumerate(reader):
            self.rows_analysed += 1
            for field_name, field in row.items():
                if field_name in self.validators:
                    for validator in self.validators[field_name]:
                        errors, warnings = validator.validate(field, row=row)
                        if errors:
                            self.errors[field_name][line].extend(errors)
                        if warnings:
                            self.warnings[field_name][line].extend(warnings)
                else:
                    self.unknown.append(field_name)

        self._gather_results()

        return self

    def _gather_results(self):

        for field, errors in self.errors.items():
            error_type_count = {}
            for line_number, errs in errors.items():
                for err in errs:
                    if err.type_ not in error_type_count:
                        error_type_count[err.type_] = 1
                    else:
                        error_type_count[err.type_] = error_type_count[err.type_] + 1
            self.report[field] = {'errors' :  error_type_count}

        for field, warnings in self.warnings.items():
            warning_type_count = {}
            for line_number, warns in warnings.items():
                for warn in warns:
                    if warn.type_ not in warning_type_count:
                        warning_type_count[warn.type_] = 1
                    else:
                        warning_type_count[warn.type_] = warning_type_count[warn.type_] + 1
            self.report[field] = {'warnings': warning_type_count}

    def error_types_for_field(self, field):
        return self.report[field]['errors']

    def warning_types_for_field(self, field):
        return self.report[field]['warnings']


class BrownfieldSiteValidator(RegisterValidator):

    valid_coordinate_reference_system = ['WGS84', 'OSGB36', 'ETRS89']
    ownership_status_pattern = r'(?i)(owned by a public authority|not owned by a public authority|unknown ownership|mixed ownership)'
    planning_status_pattern = r'(?i)(permissioned|not permissioned|pending decision)'
    permission_type_pattern = r'(?i)(full planning permission|outline planning permission|reserved matters approval|permission in principle|technical details consent|planning permission granted under an order|other)'

    validators = {
        'OrganisationURI' : [
            NotEmptyValidator(),
            URLValidator()
        ],
        'OrganisationLabel' : [
            NotEmptyValidator(),
            StringNoLineBreaksValidator()
        ],
        'SiteReference': [
            NotEmptyValidator(),
            StringNoLineBreaksValidator()
        ],
        'PreviouslyPartOf': [
            StringNoLineBreaksValidator(allow_empty=True)
        ],
        'SiteNameAddress': [
            NotEmptyValidator(),
            StringNoLineBreaksValidator()
        ],
        'SiteplanURL': [
            NotEmptyValidator(),
            URLValidator()
        ],
        'CoordinateReferenceSystem': [
            NotEmptyValidator(),
        ],
        'GeoX': [
            NotEmptyValidator(),
            FloatValidator()
        ],
        'GeoY': [
            NotEmptyValidator(),
            FloatValidator()
        ],
        'Hectares': [
            NotEmptyValidator(),
            FloatValidator()
        ],
        'OwnershipStatus': [
            NotEmptyValidator()
        ],
        'Deliverable': [],
        'PlanningStatus': [
            NotEmptyValidator()
        ],
        'PermissionType': [],
        'PermissionDate': [
            ISO8601DateValidator(allow_empty=True)
        ],
        'PlanningHistory': [
            URLValidator(allow_empty=True)
        ],
        'ProposedForPIP': [],
        'MinNetDwellings': [
            NotEmptyValidator()
        ],
        'DevelopmentDescription': [],
        'NonHousingDevelopment': [],
        'Part2': [],
        'NetDwellingsRangeFrom': [],
        'NetDwellingsRangeTo': [],
        'HazardousSubstances': [],
        'SiteInformation': [
            URLValidator(allow_empty=True)
        ],
        'Notes': [],
        'FirstAddedDate': [
            ISO8601DateValidator(),
        ],
        'LastUpdatedDate': [
            ISO8601DateValidator()
        ]
    }