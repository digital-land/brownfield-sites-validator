import csv
import io

import requests
from bs4 import UnicodeDammit

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    abort
)

from vladiate import Vlad
from vladiate.exceptions import ValidationException
from vladiate.validators import SetValidator, Validator, FloatValidator, IntValidator, Ignore
from vladiate.inputs import String


from application.frontend.forms import BrownfieldSiteURLForm

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/validate')
def validate():
    form = BrownfieldSiteURLForm(request.args)
    if form.url.data and form.validate():
        warnings, errors = _get_data_and_validate(form.url.data)
        if warnings or errors:
            return redirect(url_for('frontend.fix', url=form.url.data))
        else:
            from application.data.stubs import geojson
            return render_template('valid.html', url=form.url.data, geojson=geojson)
    return render_template('validate.html', form=form)



@frontend.route('/fix')
def fix():
    url = request.args.get('url')
    if url is None:
        return abort(403)

    if not url.endswith('.csv'):
        return abort(400)

    # in real world we stored validation result before redirection here
    warnings, errors = _get_data_and_validate(url)

    return render_template('fix.html', url=url, warnings=warnings, errors=errors)


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}


# stub method for getting data and validating
def _get_data_and_validate(url):
    warnings = []
    resp = requests.get(url)
    content_type = resp.headers.get('Content-type')
    if content_type is not None and content_type != 'text/csv':
        message = 'Expected text/csv, actual value %s' % content_type
        warnings.append(ValidatorWarning('Content-Type', message=message))

    dammit = UnicodeDammit(resp.content)
    encoding = dammit.original_encoding
    if encoding != 'utf-8':
        message = 'Expected utf-8, actual value %s' % encoding
        warnings.append(ValidatorWarning('File encoding', message=message))

    validator = BrownfieldSiteRegisterValidator(source=String(resp.content.decode(encoding)))
    validator.validate()

    # unpack the validator error messages from the exception class until we come up with something tidy?
    errors = []
    for field, failure in validator.failures.items():
        unpacked = []
        for line_no, errs in failure.items():
            unpacked.append({line_no: [message.args[0] for message in errs]})
        errors.append({field: unpacked})

    return warnings, errors


class ValidatorWarning:

    def __init__(self, name, message):
        self.name = name
        self.message = message


class URLValidator(Validator):

    def __init__(self, **kwargs):
        super(URLValidator, self).__init__(**kwargs)
        self.failures = set([])

    def validate(self, field, row={}):
        if not self.empty_ok:
            valid, exception = self.validate_url(field)
            if not valid and (field or not self.empty_ok):
                self.failures.add(field)
                raise ValidationException("{} - {}".format(field, exception))

    @property
    def bad(self):
        return self.failures

    @staticmethod
    def validate_url(url):
        from urllib.request import urlopen
        from urllib.error import URLError, HTTPError
        try:
            urlopen(url)
            return True, None
        except HTTPError as e:
            return False, e
        except URLError as e:
            return False, e.reason
        except Exception as e:
            return False, e


class StringNoLineBreaksValidator(Validator):

    def __init__(self, **kwargs):
        super(StringNoLineBreaksValidator, self).__init__(**kwargs)
        self.failures = set([])

    def validate(self, field, row={}):
        if not self.empty_ok:
            valid = self.has_no_linebreaks(field)
            if not valid and (field or not self.empty_ok):
                self.failures.add(field)
                raise ValidationException("{} - contains line breaks".format(field))

    @property
    def bad(self):
        return self.failures

    @staticmethod
    def has_no_linebreaks(field):
        if '\r\n' in field or '\n' in field:
            return False
        return True


class ISO8601DateValidator(Validator):

    def __init__(self, **kwargs):
        super(ISO8601DateValidator, self).__init__(**kwargs)
        self.failures = set([])

    def validate(self, field, row={}):
        if not self.empty_ok:
            valid, message = self.validate_date(field)
            if not valid and (field or not self.empty_ok):
                self.failures.add(field)
                raise ValidationException("{} - {}".format(field, message))

    @property
    def bad(self):
        return self.failures

    @staticmethod
    def validate_date(field):
        import datetime
        try:
            datetime.datetime.strptime(field, '%Y-%m-%d')
            return True, None
        except ValueError as e:
            return False, 'incorrect date format - should be YYYY-MM-DD'


class BrownfieldSiteRegisterValidator(Vlad):

    valid_coordinate_reference_system = ['WGS84', 'OSGB36', 'ETRS89']
    valid_ownership_status = ['owned by a public authority', 'not owned by a public authority', 'unknown ownership',
                              'mixed ownership']
    valid_planning_status = ['permissioned', 'not permissioned', 'pending decision']
    valid_permission_type = ['full planning permission',
                             'outline planning permission',
                             'reserved matters approval',
                             'permission in principle',
                             'technical details consent',
                             'planning permission granted under an order',
                             'other']

    validators = {
        'OrganisationURI' : [
            URLValidator()
        ],
        'OrganisationLabel' : [
            StringNoLineBreaksValidator()
        ],
        'SiteReference': [
            StringNoLineBreaksValidator()
        ],
        'PreviouslyPartOf': [
            StringNoLineBreaksValidator(empty_ok=True)
        ],
        'SiteNameAddress': [
            StringNoLineBreaksValidator()
        ],
        'SiteplanURL': [
            URLValidator()
        ],
        'CoordinateReferenceSystem': [
            SetValidator(valid_set=valid_coordinate_reference_system)
        ],
        'GeoX': [
            FloatValidator()
        ],
        'GeoY': [
            FloatValidator()
        ],
        'Hectares': [
            FloatValidator()
        ],
        'OwnershipStatus': [
            SetValidator(valid_set=valid_ownership_status)
        ],
        'Deliverable': [
            SetValidator(valid_set=['yes'], empty_ok=True)
        ],
        'PlanningStatus': [
            SetValidator(valid_set=valid_planning_status)
        ],
        'PermissionType': [
            SetValidator(valid_set=valid_permission_type, empty_ok=True)
        ],
        'PermissionDate': [
            ISO8601DateValidator(empty_ok=True)
        ],
        'PlanningHistory': [
            URLValidator(empty_ok=True)
        ],
        'ProposedForPIP': [
            SetValidator(valid_set=['yes'], empty_ok=True)
        ],
        'MinNetDwellings': [
            IntValidator()
        ],
        'DevelopmentDescription': [
            Ignore()
        ],
        'NonHousingDevelopment': [
            Ignore()
        ],
        'Part2': [
            SetValidator(valid_set=['yes'], empty_ok=True)
        ],
        'NetDwellingsRangeFrom': [
            IntValidator(empty_ok=True)
        ],
        'NetDwellingsRangeTo': [
            IntValidator(empty_ok=True)
        ],
        'HazardousSubstances': [
            SetValidator(valid_set=['yes'], empty_ok=True)
        ],
        'SiteInformation': [
            URLValidator(empty_ok=True)
        ],
        'Notes': [
            Ignore()
        ],
        'FirstAddedDate': [
            ISO8601DateValidator()
        ],
        'LastUpdatedDate': [
            ISO8601DateValidator()
        ]
    }


