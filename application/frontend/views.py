import requests
import json

from tempfile import NamedTemporaryFile
from bs4 import UnicodeDammit

from flask import (
    Blueprint,
    render_template,
    request,
    Response,
    redirect,
    url_for,
    current_app
)

from furl import furl
from sqlalchemy import asc

from application.validators.validators import (
    BrownfieldSiteValidationRunner,
    StringInput,
    ValidationWarning
)

from application.models import (
    Organisation,
    BrownfieldSiteValidation
)

frontend = Blueprint('frontend', __name__, template_folder='templates')


def _to_boolean(value):
    if str(value).lower() in ['1', 't', 'true', 'y', 'yes', 'on']:
        return True
    return False


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/results')
def validate_results():
    organisations = Organisation.query.order_by(asc(Organisation.name)).all()
    return render_template('results.html', organisations=organisations)


@frontend.route('/results/map')
def all_results_map():
    return render_template('results-map.html', resultdata=getAllBoundariesAndResults())


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
    if org.geojson:
        package['feature'] = org.geojson
    if org.validation and org.validation.result:
        package['csv_url'] = org.brownfield_register_url
        package['results'] = org.validation.result
    else:
        package['results'] = "No results available"

    return package


@frontend.route('/start')
def start():
    return render_template('start.html')


@frontend.route('/local-authority', methods=['GET','POST'])
def local_authority():
    if request.method == 'GET':
        organisations = Organisation.query.order_by("name").all()
        return render_template('select-la.html', organisations=organisations)
    else:
        return redirect(url_for('frontend.validate', local_authority=request.form['local-authority-selector']))


@frontend.route('/local-authority/<local_authority>/validate')
def validate(local_authority):
    if request.args.get('url') is not None:
        cached = _to_boolean(request.args.get('cached', False))
        url = request.args.get('url').strip()
        try:
            local_authority = Organisation.query.get(local_authority)
            result = get_data_and_validate(local_authority, url, cached=cached)
        except FileTypeException as e:
            current_app.logger.exception(e)
            return render_template('not-available.html',
                                   url=url,
                                   local_authority=local_authority,
                                   message=e.message)

        if (result.file_warnings and result.errors) or result.file_errors:
            return render_template('fix.html', url=url, result=result)
        else:
            return render_template('valid.html',
                                   url=url,
                                   feature=local_authority.validation.geojson(),
                                   result=result,
                                   la_boundary=local_authority.geojson)

    return render_template('validate.html', local_authority=local_authority)


@frontend.route('/geojson-download')
def geojson_download():
    if request.args.get('url') is not None:
        url = request.args.get('url').strip()
        brownfield_site = BrownfieldSiteValidation.query.filter_by(data_source=url).one()
        filename = '%s.json' % brownfield_site.organisation.organisation
        return Response(
                json.dumps(brownfield_site.geojson()),
                mimetype="application/json",
                headers={"Content-disposition":
                         "attachment; filename="+filename})

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
    publication = BrownfieldSiteValidation.query.get(brownfield_site_publication_id)
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


def get_data_and_validate(organisation, url, cached=False):

    # quick hack to use stored validation result. but maybe put timestamp on
    # db record and only use if quite fresh, otherwise fetch and update
    # stored one. Or maybe not do this at all? Just store for index page,
    # but fetch fresh each time validate view method called?
    validation = BrownfieldSiteValidation.query.filter_by(data_source=url).first()
    if validation is not None and cached:
        return BrownfieldSiteValidationRunner.from_validation(validation)
    else:
        file_warnings = []
        resp = requests.get(url)
        content_type = resp.headers.get('Content-type')
        if content_type is not None and content_type.lower() not in ['text/csv', 'text/csv;charset=utf-8']:
            file_warnings.append({'data': 'Content-Type:%s' % content_type, 'warning': ValidationWarning.CONTENT_TYPE_WARNING.to_dict()})
        resource =  furl(url).path.segments[-1]
        if 'text/csv' in content_type or resource.endswith('.csv'):
            dammit = UnicodeDammit(resp.content)
            encoding = dammit.original_encoding
            if encoding.lower() != 'utf-8':
                file_warnings.append({'data': 'File encoding: %s' % encoding, 'warning': ValidationWarning.FILE_ENCODING_WARNING.to_dict()})
            content = resp.content.decode(encoding)
            line_count = len(content.splitlines())
        else:
            content, line_count = _try_converting_to_csv(resource, resp.content)
        validator = BrownfieldSiteValidationRunner(StringInput(string_input=content), file_warnings, line_count, organisation)
        return validator.validate()
