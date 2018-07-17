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


from application.frontend.forms import BrownfieldSiteURLForm

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('start-page.html')


@frontend.route('/form')
def form():
    form = BrownfieldSiteURLForm()
    return render_template('index.html', form=form)


@frontend.route('/validation')
def validation():
    url = request.args.get('url')
    if url is None:
        return abort(403)
    result = _get_data_and_validate(url)
    if result.get('errors') or result.get('warnings'):
        return redirect(url_for('frontend.fix', url=url))
    else:
        from application.data.stubs import geojson
        return render_template('validation.html', url=url, geojson=geojson)


@frontend.route('/fix')
def fix():
    url = request.args.get('url')
    if url is None:
        return abort(403)

    # in real world we stored validation result before redirection here
    result = _get_data_and_validate(url)

    return render_template('fix.html', url=url, result=result)


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}


# stub method for getting data and validating
def _get_data_and_validate(url):
    result = {'errors': [], 'warnings': []}
    _check_file(result, url)
    return result


def _check_file(result, url):
    resp = requests.get(url)
    content_type = resp.headers.get('Content-type')
    if content_type is not None and content_type != 'text/csv':
        res = 'Expected text/csv, actual value %s' % content_type
        validation = ValidationResult('Content-Type', results=[res])
        result['warnings'].append(validation)

    dammit = UnicodeDammit(resp.content)
    encoding = dammit.original_encoding
    if encoding != 'utf-8':
        res = 'Expected utf-8, actual value %s' % encoding
        validation = ValidationResult('File encoding', results=[res])
        result['warnings'].append(validation)

    reader = csv.DictReader(io.StringIO(resp.content.decode(encoding)))

    # just for the moment hobble the file to see validation error
    fields = reader.fieldnames[0:5]

    missing = set(required_fields).difference(set(fields))
    if missing:
        validation = ValidationResult('Missing fields', results=list(missing))
        result['errors'].append(validation)

    # just to mess with validation
    fields.append('SomethingRandom')

    extra = set(fields).difference(set(required_fields))
    if extra:
        validation = ValidationResult('Extra fields', results=list(extra))
        result['errors'].append(validation)


required_fields = ['OrganisationURI',
                   'OrganisationLabel',
                   'SiteReference',
                   'PreviouslyPartOf',
                   'SiteNameAddress',
                   'SiteplanURL',
                   'CoordinateReferenceSystem',
                   'GeoX',
                   'GeoY',
                   'Hectares',
                   'OwnershipStatus',
                   'Deliverable',
                   'PlanningStatus',
                   'PermissionType',
                   'PermissionDate',
                   'PlanningHistory',
                   'ProposedForPIP',
                   'MinNetDwellings',
                   'DevelopmentDescription',
                   'NonHousingDevelopment',
                   'Part2',
                   'NetDwellingsRangeFrom',
                   'NetDwellingsRangeTo',
                   'HazardousSubstances',
                   'SiteInformation',
                   'Notes',
                   'FirstAddedDate',
                   'LastUpdatedDate']


class ValidationResult:

    def __init__(self, name, results):
        self.name = name
        self.results = results
