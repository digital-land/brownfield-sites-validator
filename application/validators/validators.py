"""
    Sketch of a validation approach for csv files.
    Heavily influenced by (that is to say, ripped off from https://github.com/di/vladiate)
"""

import csv
import json
import logging
import re
import requests

from io import StringIO
from enum import Enum

from bng_to_latlon import OSGB36toWGS84
from requests.exceptions import InvalidSchema, HTTPError, MissingSchema
from sqlalchemy import func, and_

from application.models import Feature

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ValidationError(Enum):

    INVALID_URL = 'An invalid URL was found in the file'
    INVALID_DATE = 'Date format should be YYYY-MM-DD'
    NO_LINE_BREAK = 'No line breaks allowed'
    REQUIRED_FIELD = 'Required data is missing'
    INVALID_FLOAT = 'This field must contain a floating point number'
    INVALID_CSV_HEADERS = 'This file does not contain the expected headers'
    INVALID_CONTENT = 'This field does not contain expected content'

    def to_dict(self):
        return {'type': self.name, 'message': self.value}


class ValidationWarning(Enum):

    HTTP_WARNING = 'There was a problem fetching data from a URL in the file'
    DATE_WARNING = 'The date is in the future. Please check'
    CONTENT_TYPE_WARNING = 'Set Content-Type to test/csv;charset-utf8'
    FILE_ENCODING_WARNING = 'File should be encoded as utf-8'
    LOCATION_WARNING = 'Site location is not within expected area'

    def to_dict(self):
        return {'type': self.name, 'message': self.value}


class StringInput():

    ''' Read a file from a string '''

    def __init__(self, string_input=None, string_io=None):
        self.string_io = string_io if string_io else StringIO(string_input)

    def open(self):
        return self.string_io


# TODO CrossfieldValidator, convert files if needed e.g. xls/xlsm -> csv then validate


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

    def validate(self, field, row):
        errors = []
        warnings = []
        data = row.get(field)
        if data is not None and not self.allow_empty and data not in self.checked:
            try:
                resp = requests.head(data)
                resp.raise_for_status()
                self.checked.add(data)
            except (InvalidSchema, MissingSchema) as e:
                errors.append({'data': data, 'error': ValidationError.INVALID_URL.to_dict(), 'message' : str(e)})
                logger.info('Found error with', data)
            except HTTPError as e:
                warnings.append({'data': data, 'warning': ValidationWarning.HTTP_WARNING.to_dict(), 'message' : str(e)})
                logger.info('Found warning with', data)

        return errors, warnings


class StringNoLineBreaksValidator(BaseFieldValidator):

    ''' Field cannot contain line breaks '''

    def __init__(self, **kwargs):
        super(StringNoLineBreaksValidator, self).__init__(**kwargs)

    def validate(self, field, row):
        errors = []
        warnings = []
        data = row.get(field)
        if data is not None and ('\r\n' in data or '\n' in data):
            errors.append({'data': data, 'error': ValidationError.NO_LINE_BREAK.to_dict()})
            logger.info('Found error with', data)
        return errors, warnings


class ISO8601DateValidator(BaseFieldValidator):

    ''' Field must be iso-8601 formatted date string '''

    def __init__(self, **kwargs):
        super(ISO8601DateValidator, self).__init__(**kwargs)

    def validate(self, field, row):
        import datetime
        errors = []
        warnings = []
        data = row.get(field)
        if data is not None and not self.allow_empty:
            try:
                datetime.datetime.strptime(data, '%Y-%m-%d')
            except ValueError as e:
                errors.append({'data': data, 'error': ValidationError.INVALID_DATE.to_dict()})
                logger.info('Found error with', data)

        return errors, warnings


class NotEmptyValidator(BaseFieldValidator):

    ''' Field cannot be empty '''

    def __init__(self, **kwargs):
        super(NotEmptyValidator, self).__init__(**kwargs)

    def validate(self, field, row):
        errors = []
        warnings = []
        data = row.get(field)
        if data is not None and data.strip() == '':
            errors.append({'data': data, 'error': ValidationError.REQUIRED_FIELD.to_dict()})
            logger.info('Found error with', data)
        return errors, warnings


class FloatValidator(BaseFieldValidator):

    def __init__(self, **kwargs):
        super(FloatValidator, self).__init__(**kwargs)

    def validate(self, field, row):
        errors = []
        warnings = []
        data = row.get(field)
        try:
            if data is not None:
                float(data)
        except ValueError as e:
            errors.append({'data': data, 'error': ValidationError.INVALID_FLOAT.to_dict()})
            logger.info('Found error with', data)
        return errors, warnings


class GeoXFieldValidator(BaseFieldValidator):

    ''' Checks location of GeoX in conjunction GeoY '''

    def __init__(self, organisation, check_against, **kwargs):
        super(GeoXFieldValidator, self).__init__(**kwargs)
        self.organisation = organisation
        self.check_against = check_against

    def validate(self, field, row):
        errors = []
        warnings = []
        try:
            geoX = float(field)
            geoY = float([self.check_against])

            if row['CoordinateReferenceSystem'] == 'OSGB36':
                lat, lng = OSGB36toWGS84(geoX, geoY)
            else:
                lng, lat = geoX, geoY

            point = func.ST_SetSRID(func.ST_MakePoint(lng,lat), 4326)
            f = Feature.query.filter(and_(Feature.geometry.ST_Contains(point), Feature.feature==self.organisation.feature.feature)).first()
            if f is None:
                raise ValueError('Point is not within borough')
        except ValueError as e:
            message = 'This field was validated in conjunction with %s' % self.check_against
            warnings.append({'data': field, 'warning': ValidationWarning.LOCATION_WARNING.to_dict(), 'message': message})
            print('Found warning with', field, e)

        return errors, warnings


class RegexValidator(BaseFieldValidator):

    def __init__(self, expected, **kwargs):
        super(RegexValidator, self).__init__(**kwargs)
        self.expected = expected
        pattern = r'(?i)(%s)' % '|'.join(self.expected)
        self.regex = re.compile(pattern)

    def validate(self, field, row):
        errors = []
        warnings = []
        data = row.get(field)
        if data or not self.allow_empty:
            if self.regex.match(data) is None:
                message = 'Content should be one of: %s' % ','.join(self.expected)
                errors.append({'data': data, 'error': ValidationError.INVALID_CONTENT.to_dict(), 'message' : message})
                logger.info('Found error with', data)
        return errors, warnings


class ValidationRunner:

    def __init__(self, source, file_warnings, line_count, organisation, validators={}, delimiter=None):

        self.source = source
        self.file_warnings = file_warnings
        self.file_errors = []
        self.line_count = line_count
        self.errors = {}
        self.warnings = {}
        self.missing = []
        self.unknown = []
        self.validators = validators or getattr(self, 'validators', {})
        self.delimiter = delimiter or getattr(self, 'delimiter', ',')
        self.rows_analysed = 0
        self.report = {}
        self.organisation = organisation
        self.empty_lines = 0

    def to_dict(self):
        return {'errors': self.errors,
                'warnings': self.warnings,
                'file_errors': self.file_errors,
                'file_warnings': self.file_warnings,
                'missing': list(self.missing),
                'unknown': list(self.unknown),
                'line_count': self.line_count,
                'rows_analysed': self.rows_analysed,
                'report': self.report,
                'empty_lines': self.empty_lines}

    @classmethod
    def from_site(cls, site):
        datadict = site.validation_result
        validator = cls(None, file_warnings=datadict['file_warnings'], line_count=datadict['line_count'], organisation=site.organisation)
        validator.errors = datadict['errors']
        validator.warnings = datadict['warnings']
        validator.missing = datadict['missing']
        validator.unknown = datadict['unknown']
        validator.rows_analysed = datadict['rows_analysed']
        validator.report = datadict['report']
        validator.empty_lines = datadict['empty_lines']
        return validator

    def validate(self):

        reader = csv.DictReader(self.source.open(), delimiter=self.delimiter)

        validator_fields = []
        for key, val in self.validators.items():
            if isinstance(key, tuple):
                for k in key:
                    validator_fields.append(k)
            else:
                validator_fields.append(key)

        expected_fields = set(validator_fields)
        optional_additional_fields = ['Northing', 'NORTHING', 'Easting', 'EASTING']

        self.missing = list(expected_fields - set(reader.fieldnames))
        self.unknown = list(set(reader.fieldnames) - expected_fields)
        self.unknown = list(set(self.unknown) - set(optional_additional_fields))

        # if this happens, then file headers are completely broken and no point carrying on
        if self.missing == set(self.validators):
            self.file_errors = {'data': 'file', 'error': ValidationError.INVALID_CSV_HEADERS.to_dict()}
            self.unknown = set(reader.fieldnames)
            return None

        for line, row in enumerate(reader):
            if all(v.strip() == '' for v in row.values()):
                self.empty_lines += 1
                continue
            self.rows_analysed += 1
            for field, validators in self.validators.items():
                for validator in validators:
                    errors, warnings = validator.validate(field, row)
                    if errors:
                        if self.errors.get(field) is None:
                            self.errors[field] = {}
                        if self.errors[field].get(line) is None:
                            self.errors[field][line] = []
                        self.errors[field][line].extend(errors)
                    if warnings:
                        if self.warnings.get(field) is None:
                            self.warnings[field] = {}
                        if self.warnings[field].get(line) is None:
                            self.warnings[field][line] = []
                        self.warnings[field][line].extend(warnings)

        self._gather_results()

    def _gather_results(self):

        for field, errors in self.errors.items():
            error_type_count = {}
            for line_number, errs in errors.items():
                for err in errs:
                    err_type = err['error']['type']
                    if err_type not in error_type_count:
                        error_type_count[err_type] = 1
                    else:
                        error_type_count[err_type] = error_type_count[err_type] + 1
            self.report[field] = {'errors' :  error_type_count}

        for field, warnings in self.warnings.items():
            warning_type_count = {}
            for line_number, warns in warnings.items():
                for warn in warns:
                    warn_type = warn['warning']['type']
                    if warn_type not in warning_type_count:
                        warning_type_count[warn_type] = 1
                    else:
                        warning_type_count[warn_type] = warning_type_count[warn_type] + 1
            self.report[field] = {'warnings': warning_type_count}


class BrownfieldSiteValidationRunner(ValidationRunner):

    def __init__(self, source, file_warnings, line_count, organisation):

        super(BrownfieldSiteValidationRunner, self).__init__(source, file_warnings, line_count, organisation)

        valid_coordinate_reference_system = ['WGS84', 'OSGB36', 'ETRS89']
        valid_ownership_status = ['owned by a public authority',
                                  'not owned by a public authority',
                                  'unknown ownership','mixed ownership']
        valid_planning_status = ['permissioned', 'not permissioned', 'pending decision']
        valid_permission_type = ['full planning permission',
                                 'outline planning permission',
                                 'reserved matters approval',
                                 'permission in principle',
                                 'technical details consent',
                                 'planning permission granted under an order',
                                 'other']

        self.validators = {
            'OrganisationURI': [
                NotEmptyValidator(),
                URLValidator()
            ],
            'OrganisationLabel': [
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
                RegexValidator(expected=valid_coordinate_reference_system),
            ],
            'GeoX': [
                NotEmptyValidator(),
                FloatValidator(),
                GeoXFieldValidator(self.organisation, check_against='GeoY')
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
                NotEmptyValidator(),
                RegexValidator(expected=valid_ownership_status)
            ],
            'Deliverable': [],
            'PlanningStatus': [
                NotEmptyValidator(),
                RegexValidator(expected=valid_planning_status)
            ],
            'PermissionType': [
                RegexValidator(expected=valid_permission_type, allow_empty=True)
            ],
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
