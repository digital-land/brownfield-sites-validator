"""
    Sketch of a validation approach for csv files.
    Heavily influenced by (that is to say, ripped off from https://github.com/di/vladiate)
"""

import csv
import logging
import re
import requests

from io import StringIO
from collections import defaultdict
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


class GeoXYFieldValidator(BaseFieldValidator):

    ''' Checks geo point field in conjunction with another field in this row '''

    def __init__(self, organisation, **kwargs):
        super(GeoXYFieldValidator, self).__init__(**kwargs)
        self.organisation = organisation

    def validate(self, field, row):
        # data = row.get('field')
        # TODO need to work out location of borough to check in co-ordinates
        # are in the borough - maybe this validator is a geovalidator that is a subclass
        # of a crossfield validator?
        errors = []
        warnings = []
        if isinstance(field, tuple):
            try:
                geoX = float(row[field[0]])
                geoY = float(row[field[1]])

                if row['CoordinateReferenceSystem'] == 'OSGB36':
                    lat, lng = OSGB36toWGS84(geoX, geoY)
                else:
                    lng, lat = geoX, geoY

                point = func.ST_SetSRID(func.ST_MakePoint(lng,lat), 4326)
                f = Feature.query.filter(and_(Feature.geometry.ST_Contains(point), Feature.feature==self.organisation.feature.feature)).first()
                if f is None:
                    raise ValueError('Point is not within borough')
            except ValueError as e:
                warnings.append({'data': field, 'warning': ValidationWarning.LOCATION_WARNING.to_dict()})
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
        self.errors = defaultdict(lambda: defaultdict(list))
        self.warnings = defaultdict(lambda: defaultdict(list))
        self.missing = []
        self.unknown = []
        self.validators = validators or getattr(self, 'validators', {})
        self.delimiter = delimiter or getattr(self, 'delimiter', ',')
        self.rows_analysed = 0
        self.report = {}
        self.organisation = organisation

    def to_dict(self):
        return {'errors': self.errors,
                'warnings': self.warnings,
                'file_errors': self.file_errors,
                'file_warnings': self.file_warnings,
                'missing': list(self.missing),
                'unknown': list(self.unknown),
                'line_count': self.line_count,
                'rows_analysed': self.rows_analysed,
                'report': self.report}

    @classmethod
    def from_dict(cls, site):
        datadict = site.validation_result
        validator = cls(None, file_warnings=datadict['file_warnings'], line_count=datadict['line_count'])
        validator.errors = datadict['errors']
        validator.warnings = datadict['warnings']
        validator.missing = datadict['missing']
        validator.unknown = datadict['unknown']
        validator.rows_analysed = datadict['rows_analysed']
        validator.report = datadict['report']
        validator.organisation = site.organisation
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

        self.missing = set(validator_fields) - set(reader.fieldnames)
        self.unknown = set(reader.fieldnames) - set(validator_fields)

        # if this happens, then file headers are completely broken and no point carrying on
        if self.missing == set(self.validators):
            self.file_errors = {'data': 'file', 'error': ValidationError.INVALID_CSV_HEADERS.to_dict()}
            self.unknown = set(reader.fieldnames)
            return self

        for line, row in enumerate(reader):
            self.rows_analysed += 1
            for field, validators in self.validators.items():
                for validator in validators:
                    errors, warnings = validator.validate(field, row)
                    if errors:
                        self.errors[field][line].extend(errors)
                    if warnings:
                        self.warnings[field][line].extend(warnings)

        self._gather_results()

        return self

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
            ('GeoX', 'GeoY'): [
                NotEmptyValidator(),
                FloatValidator(),
                GeoXYFieldValidator(self.organisation)
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
