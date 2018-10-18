import requests

from tempfile import NamedTemporaryFile
from bs4 import UnicodeDammit

from flask import (
    Blueprint,
    render_template,
    request,
    current_app,
    abort
)
from furl import furl

from sqlalchemy import asc

from application.validators.validators import (
    BrownfieldSiteValidationRunner,
    StringInput,
    ValidationWarning
)

from application.models import BrownfieldSitePublication, Organisation, Feature


frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/results')
def validate_results():
    publications = BrownfieldSitePublication.query.join(Organisation).order_by(asc(Organisation.name))
    return render_template('results.html', publications=publications)

@frontend.route('/results/map')
def all_results_map():
    publications = BrownfieldSitePublication.query.join(Organisation).order_by(asc(Organisation.name))
    features = Feature.query.all()
    featureGeoJson = []
    for feature in features:
        featureGeoJson.append(feature.geojson)
    data = getAllBoundariesAndResults()
    return render_template('results-map.html', featureGeoJson=featureGeoJson, resultdata=data)


def getAllBoundariesAndResults():
    organisations = Organisation.query.all()
    data = []
    for org in organisations:
        data.append( getBoundaryAndResult(org) )
    return data

def getBoundaryAndResult(org):
    package = {}
    package['org_id'] = org.organisation
    package['org_name'] = org.name
    if org.feature and org.feature.geojson:
        package['feature'] = org.feature.geojson
    if org.publication and org.publication.validation and org.publication.validation.result:
        package['csv_url'] = org.publication.data_url
        publication = BrownfieldSitePublication.query.filter_by(organisation_id=org.organisation).one()
        package['results'] = publication.validation.result
    else:
        package['results'] = "No results available"

    return package

@frontend.route('/start')
def start():
    return render_template('start.html')


def _to_boolean(value):
    if str(value).lower() in ['1', 't', 'true', 'y', 'yes', 'on']:
        return True
    return False


@frontend.route('/validate')
def validate():
    if request.args.get('url') is not None:
        cached = _to_boolean(request.args.get('cached', False))
        url = request.args.get('url').strip()
        try:
            result = _get_data_and_validate(url, cached=cached)
        except FileTypeException as e:
            current_app.logger.exception(e)
            return render_template('not-available.html',
                                   url=url,
                                   message=e.message)

        brownfield_site = BrownfieldSitePublication.query.filter_by(data_url=url).one()

        if (result.file_warnings and result.errors) or result.file_errors:
            return render_template('fix.html', url=url, result=result, brownfield_site=brownfield_site)
        else:
            la_boundary=brownfield_site.organisation.feature.geojson
            return render_template('valid.html',
                                   url=url,
                                   feature=brownfield_site.geojson,
                                   result=result,
                                   la_boundary=la_boundary)

    return render_template('validate.html')

#@frontend.route('/fix-up/<brownfield_site_publication_id>')
@frontend.route('/fix-up/task-list')
def task_list():
    return render_template('fix-task-list.html')

#@frontend.route('/fix-up/<brownfield_site_publication_id>/fix-columns')
@frontend.route('/fix-up/task-list/fix-columns')
def fix_columns():
    return render_template('fix-column-issues.html')

#@frontend.route('/fix-up/<brownfield_site_publication_id>/fix-dates')
@frontend.route('/fix-up/task-list/fix-dates')
def fix_dates():
    return render_template('fix-data-issues.html')

@frontend.route('/fix-up/<brownfield_site_publication_id>/geography')
def fix_up_geography(brownfield_site_publication_id):
    publication = BrownfieldSitePublication.query.get(brownfield_site_publication_id)
    return render_template('fix-up-geography.html', brownfield_site_publication=publication)


@frontend.route('/error')
def error():
    return render_template('not-available.html')


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}


@frontend.context_processor
def asset_path_context_processor():
    return {'assetPath': '/static/govuk-frontend/assets'}


class FileTypeException(Exception):

    def __init__(self, message):
        self.message = message


def _try_converting_to_csv(path, content):
    import subprocess
    with NamedTemporaryFile(delete=False) as file:
        file.write(content)
        file_name = file.name

    csv_file = '%s.csv' % file_name

    try:

        if path.endswith('.xls') or path.endswith('.xlsx'):
            with open(csv_file, 'wb') as out:
                subprocess.check_call(['in2csv', file_name], stdout=out)

        elif path.endswith('.xlsm'):
            with open(csv_file, 'wb') as out:
                subprocess.check_call(['xlsx2csv', file_name], stdout=out)

        else:
            msg = 'Not sure how to convert the file %s' % path
            raise FileTypeException(msg)

        with open(csv_file, 'r') as file:
            content = file.readlines()

        return '\n'.join(content), len(content)

    except Exception as e:
        msg = 'Could not convert %s into csv' % path
        raise FileTypeException(msg)

def _get_data_and_validate(url, cached=False):

    # quick hack to use stored validation result. but maybe put timestamp on
    # db record and only use if quite fresh, otherwise fetch and update
    # stored one. Or maybe not do this at all? Just store for index page,
    # but fetch fresh each time validate view method called?
    publication = BrownfieldSitePublication.query.filter_by(data_url=url).first()
    if publication is not None and publication.validation is not None and cached:
        return BrownfieldSiteValidationRunner.from_publication(publication)
    else:
        file_warnings = []
        resp = requests.get(url)
        content_type = resp.headers.get('Content-type')
        if content_type is not None and content_type.lower() not in ['text/csv', 'text/csv;charset=utf-8']:
            file_warnings.append({'data': 'Content-Type:%s' % content_type, 'warning': ValidationWarning.CONTENT_TYPE_WARNING.to_dict()})
        resource =  furl(url).path.segments[-1]
        if resource.endswith('.csv'):
            dammit = UnicodeDammit(resp.content)
            encoding = dammit.original_encoding
            if encoding.lower() != 'utf-8':
                file_warnings.append({'data': 'File encoding: %s' % encoding, 'warning': ValidationWarning.FILE_ENCODING_WARNING.to_dict()})
            content = resp.content.decode(encoding)
            line_count = len(content.splitlines())
        else:
            content, line_count = _try_converting_to_csv(resource, resp.content)

        publication = BrownfieldSitePublication.query.filter_by(data_url=url).first()
        validator = BrownfieldSiteValidationRunner(StringInput(string_input=content), file_warnings, line_count, publication)
        return validator.validate()
