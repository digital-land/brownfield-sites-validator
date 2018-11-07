"""
    Sketch of a validation approach for csv files.
    Heavily influenced by (that is to say, ripped off from https://github.com/di/vladiate)
"""

import csv
import datetime
import logging
import re
import uuid
from urllib.parse import urlparse

import pyproj
import requests

from io import StringIO
from enum import Enum

from requests.exceptions import InvalidSchema, HTTPError, MissingSchema
from sqlalchemy import func, and_

from application.models import BrownfieldSiteValidation, Organisation
from application.extensions import db

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
    CONTENT_TYPE_WARNING = 'Set Content-Type to text/csv;charset-utf8'
    FILE_ENCODING_WARNING = 'File should be encoded as utf-8'
    LOCATION_WARNING = 'Site location is not within expected area'
    CONTENT_WARNING = 'There is better content for this field'

    def to_dict(self):
        return {'type': self.name, 'message': self.value}


class StringInput():

    def __init__(self, string_input=None, string_io=None):
        self.string_io = string_io if string_io else StringIO(string_input)

    def open(self):
        return self.string_io


class BaseFieldValidator:

    def __init__(self, allow_empty=False):
        self.allow_empty = allow_empty

    def validate(self, field, row):
        raise NotImplementedError


class URLValidator(BaseFieldValidator):

    def __init__(self, check_exists=False, **kwargs):
        super(URLValidator, self).__init__(**kwargs)
        self.checked = set([])
        self.check_exists = check_exists

    def validate(self, field, row):
        data = row.get(field)
        if data != '' or (data and not self.allow_empty):
            result = urlparse(data)
            if all([result.scheme, result.netloc]):
                return {'data': data}
            else:
                return {'data': data, 'error': ValidationError.INVALID_URL.to_dict()}
            if self.check_exists and data not in self.checked:
                try:
                    resp = requests.head(data, timeout=6)
                    resp.raise_for_status()
                    self.checked.add(data)
                except (InvalidSchema, MissingSchema) as e:
                    logger.debug('Found error with', data)
                    return {'data': data, 'error': ValidationError.INVALID_URL.to_dict()}
                except (HTTPError, requests.exceptions.ConnectionError) as e:
                    logger.debug('Found warning with', data)
                    return {'data': data, 'warning': ValidationWarning.HTTP_WARNING.to_dict()}

        return {'data': data}


class StringNoLineBreaksValidator(BaseFieldValidator):

    def __init__(self, **kwargs):
        super(StringNoLineBreaksValidator, self).__init__(**kwargs)

    def validate(self, field, row):

        data = row.get(field)

        if data is not None and not self.allow_empty and ('\r\n' in data or '\n' in data):
            fix = data.replace('\r\n',',').replace('\n', ',')
            logger.info('Found error with', data)
            return {'data': data, 'error': ValidationError.NO_LINE_BREAK.to_dict(), 'fix': fix}

        return {'data': data}


class ISO8601DateValidator(BaseFieldValidator):

    def __init__(self, fixer, **kwargs):
        super(ISO8601DateValidator, self).__init__(**kwargs)
        self.fixer = fixer

    def validate(self, field, row):

        data = row.get(field).replace('"', '').replace("'", '')
        if data is not None and not self.allow_empty:
            try:
                datetime.datetime.strptime(data, '%Y-%m-%d')
            except ValueError as e:
                fix = self.fixer(data)
                logger.info('Found error with', data)
                return {'data': data, 'error': ValidationError.INVALID_DATE.to_dict(), 'fix': fix}

        return {'data': data}


class NotEmptyValidator(BaseFieldValidator):

    def __init__(self, **kwargs):
        super(NotEmptyValidator, self).__init__(**kwargs)

    def validate(self, field, row):
        errors = []
        warnings = []
        data = row.get(field)
        if data is None or data.strip() == '':
            return {'data': data, 'error': ValidationError.REQUIRED_FIELD.to_dict()}
        return {'data': data}


class FloatValidator(BaseFieldValidator):

    def __init__(self, **kwargs):
        super(FloatValidator, self).__init__(**kwargs)

    def validate(self, field, row):
        data = row.get(field)
        try:
            if data is not None and not self.allow_empty :
                float(data)
        except ValueError as e:
            logger.info('Found error with', data)
            return {'data': data, 'error': ValidationError.INVALID_FLOAT.to_dict()}

        return {'data': data}


class GeoFieldValidator(BaseFieldValidator):

    ''' Checks location of GeoX in conjunction GeoY '''

    def __init__(self, organisation, check_against, **kwargs):
        super(GeoFieldValidator, self).__init__(**kwargs)
        self.organisation = organisation
        self.check_against = check_against

    def validate(self, field, row):

        if field == 'GeoX':
            geoX = float(row[field].strip())
            geoY = float(row[self.check_against].strip())
        elif field == 'GeoY':
            geoX = float(row[self.check_against].strip())
            geoY = float(row[field].strip())

        if row.get('CoordinateReferenceSystem') == 'OSGB36' or geoY > 10000.0:
            bng = pyproj.Proj(init='epsg:27700')
            wgs84 = pyproj.Proj(init='epsg:4326')
            lng, lat = pyproj.transform(bng, wgs84, geoX, geoY)
        else:
            lng, lat = geoX, geoY

        point = func.ST_SetSRID(func.ST_MakePoint(lng,lat), 4326)
        f = Organisation.query.filter(and_(Organisation.geometry.ST_Contains(point),
                                           Organisation.organisation == self.organisation.organisation)).first()

        if f is None:
            if field == 'GeoX' and not (-5.5 < lng < 1.9):
                fix = lat
            elif field == 'GeoY' and not (49.0 < lat < 55.5):
                fix = lng
            else:
                fix = None
        else:
            if field == 'GeoX':
                fix = lng
            elif field == 'GeoY':
                fix = lat
            else:
                fix = None

        result = {'data': row.get(field), 'fix': fix}

        if f is None:
            result['warning'] = ValidationWarning.LOCATION_WARNING.to_dict()

        return result


class RegexValidator(BaseFieldValidator):

    def __init__(self, expected, fixer=None, **kwargs):
        super(RegexValidator, self).__init__(**kwargs)
        self.expected = expected
        pattern = r'(?i)(%s)' % '|'.join(self.expected)
        self.regex = re.compile(pattern)
        self.fixer = fixer

    def validate(self, field, row):
        data = row.get(field)
        fix = self.fixer(data) if self.fixer else None
        if data is not None and not self.allow_empty:
            if self.regex.match(data) is None:
                logger.info('Found error with', data)
                message = 'Content should be one of: %s' % ','.join(self.expected)
                return {'data': data,
                        'error': ValidationError.INVALID_CONTENT.to_dict(),
                        'fix': fix}

        result = {'data': data, 'fix': fix}
        if self.fixer is not None and data != fix:
            result['warning'] = ValidationWarning.CONTENT_WARNING.to_dict()

        return result


class ValidationRunner:

    def __init__(self, source, file_warnings, line_count, organisation, validators={}, delimiter=None):

        self.source = source
        self.file_warnings = file_warnings
        self.file_errors = []
        self.line_count = line_count
        self.errors = False
        self.warnings = False
        self.missing = []
        self.unknown = []
        self.validators = validators or getattr(self, 'validators', {})
        self.delimiter = delimiter or getattr(self, 'delimiter', ',')
        self.rows_analysed = 0
        self.report = {}
        self.empty_lines = 0
        self.validated_rows = []
        self.organisation = organisation
        self.has_geo_fixes = False

    def to_dict(self):
        return {'file_errors': self.file_errors,
                'file_warnings': self.file_warnings,
                'errors': self.errors,
                'warnings': self.warnings,
                'missing': list(self.missing),
                'unknown': list(self.unknown),
                'line_count': self.line_count,
                'rows_analysed': self.rows_analysed,
                'report': self.report,
                'empty_lines': self.empty_lines,
                'has_geo_fixes': self.has_geo_fixes}

    @classmethod
    def from_validation(cls, validation):
        datadict = validation.result
        validator = cls(None, datadict['file_warnings'], datadict['line_count'], validation.organisation)
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

        if set(self.missing) == set(self.validators):
            self.file_errors = {'data': 'file', 'error': ValidationError.INVALID_CSV_HEADERS.to_dict()}
            self.unknown = set(reader.fieldnames)
        else:
            for line, row in enumerate(reader):
                if all(v.strip() == '' for v in row.values()):
                    self.empty_lines += 1
                    continue
                self.rows_analysed += 1
                validated = {'line': line, 'content': row, 'validation_result': {}}
                for field, validators in self.validators.items():
                    for validator in validators:
                        result = validator.validate(field, row)
                        validated['validation_result'][field] = result

                self.validated_rows.append(validated)

        self._gather_result_counts()

        url = self.organisation.brownfield_register_url if self.organisation.brownfield_register_url else None

        validation = BrownfieldSiteValidation(id=uuid.uuid4(),
                                              data_source=url,
                                              result=self.to_dict(),
                                              data=self.validated_rows)

        self.organisation.validation_results.append(validation)

        db.session.add(self.organisation)
        db.session.commit()

        return validation

    def _gather_result_counts(self):

        for item in self.validated_rows:
            for field, result in item['validation_result'].items():
                if result.get('error') is not None:
                    self.errors = True
                    if self.report.get(field) is None:
                        self.report[field] = {'errors': {}}
                    err_type = result['error']['type']
                    if self.report[field]['errors'].get(err_type) is None:
                        self.report[field]['errors'][err_type] = 1
                    else:
                        self.report[field]['errors'][err_type] += 1
                if result.get('warning') is not None:
                    self.warnings = True
                    if self.report.get(field) is None:
                        self.report[field] = {'warnings': {}}
                    warning_type = result['warning']['type']
                    if warning_type == ValidationWarning.LOCATION_WARNING.name and result.get('fix') is not None:
                        self.has_geo_fixes = True
                    if self.report[field]['warnings'].get(warning_type) is None:
                        self.report[field]['warnings'][warning_type] = 1
                    else:
                        self.report[field]['warnings'][warning_type] += 1


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

        def set_osgb36_to_wgs84(coordinate_reference_system):
            if coordinate_reference_system == 'OSGB36':
                return 'WGS84'
            return coordinate_reference_system

        def date_fix(data):
            try:
                d = datetime.datetime.strptime(data, '%d/%m/%Y')
                return datetime.date.strftime(d, '%Y-%m-%d')
            except ValueError:
                return None

        self.validators = {
            'OrganisationURI': [
                URLValidator()
            ],
            'OrganisationLabel': [
                StringNoLineBreaksValidator()
            ],
            'SiteReference': [
                StringNoLineBreaksValidator()
            ],
            'PreviouslyPartOf': [
                StringNoLineBreaksValidator(allow_empty=True)
            ],
            'SiteNameAddress': [
                StringNoLineBreaksValidator()
            ],
            'SiteplanURL': [
                URLValidator()
            ],
            'CoordinateReferenceSystem': [
                RegexValidator(expected=valid_coordinate_reference_system, fixer=set_osgb36_to_wgs84),
            ],
            'GeoX': [
                GeoFieldValidator(self.organisation, check_against='GeoY')
            ],
            'GeoY': [
                GeoFieldValidator(self.organisation, check_against='GeoX')
            ],
            'Hectares': [
                FloatValidator()
            ],
            'OwnershipStatus': [
                RegexValidator(expected=valid_ownership_status)
            ],
            'Deliverable': [],
            'PlanningStatus': [
                RegexValidator(expected=valid_planning_status)
            ],
            'PermissionType': [
                RegexValidator(expected=valid_permission_type, allow_empty=True)
            ],
            'PermissionDate': [
                ISO8601DateValidator(allow_empty=True, fixer=date_fix)
            ],
            'PlanningHistory': [
                URLValidator(allow_empty=True)
            ],
            'ProposedForPIP': [],
            'MinNetDwellings': [
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
                ISO8601DateValidator(fixer=date_fix),
            ],
            'LastUpdatedDate': [
                ISO8601DateValidator(fixer=date_fix)
            ]
        }
