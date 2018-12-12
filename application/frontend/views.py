import csv
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

from application.extensions import db, flask_optimize
from application.frontend.forms import UploadForm
from application.validators.validators import (
    BrownfieldSiteValidationRunner,
    StringInput,
    ValidationWarning
)

from application.models import BrownfieldSiteRegister, StaticContent

frontend = Blueprint('frontend', __name__, template_folder='templates')


def _to_boolean(value):
    if str(value).lower() in ['1', 't', 'true', 'y', 'yes', 'on']:
        return True
    return False


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/results')
@flask_optimize.optimize()
def validate_results():
    page = StaticContent.query.get('results-static')
    if page is not None:
        return page.content.encode('utf-8').strip()
    else:
        return render_template('no-results-yet.html')


@frontend.route('/results-dynamic')
def validate_results_dynamic():
    registers = db.session.query(BrownfieldSiteRegister.organisation,
                                 BrownfieldSiteRegister.name,
                                 BrownfieldSiteRegister.geojson,
                                 BrownfieldSiteRegister.validation_result,
                                 BrownfieldSiteRegister.validation_created_date).order_by(asc(BrownfieldSiteRegister.name)).all()
    return render_template('results.html', registers=registers)


@frontend.route('/results/map')
@flask_optimize.optimize()
def all_results_map():
    page = StaticContent.query.get('results-map-static')
    if page is not None:
        return page.content.encode('utf-8').strip()
    else:
        return render_template('no-results-yet.html')


@frontend.route('/results/map-dynamic')
def all_results_map_dynamic():
    return render_template('results-map.html', resultdata=get_all_boundaries_and_results())


def get_all_boundaries_and_results():
    registers = db.session.query(BrownfieldSiteRegister.organisation,
                                 BrownfieldSiteRegister.name,
                                 BrownfieldSiteRegister.geojson,
                                 BrownfieldSiteRegister.validation_result,
                                 BrownfieldSiteRegister.register_url,
                                 BrownfieldSiteRegister.validation_created_date).order_by(
        asc(BrownfieldSiteRegister.name)).all()
    data = []
    for reg in registers:
        data.append(get_boundary_and_result(reg))
    return data


def get_boundary_and_result(register):
    package = {}
    package['org_id'] = register.organisation
    package['org_name'] = register.name
    if register.geojson:
        package['feature'] = register.geojson
    if register.validation_result:
        package['csv_url'] = register.register_url
        package['results'] = register.validation_result
    else:
        package['results'] = "No results available"

    return package


@frontend.route('/start')
def start():
    return render_template('start.html')


@frontend.route('/local-authority', methods=['GET','POST'])
def local_authority():
    if request.method == 'GET':
        registers = db.session.query(BrownfieldSiteRegister.organisation,
                                     BrownfieldSiteRegister.name).order_by(
            asc(BrownfieldSiteRegister.name)).all()
        return render_template('select-la.html', registers=registers)
    else:
        return redirect(url_for('frontend.validate', local_authority=request.form['local-authority-selector']))


@frontend.route('/local-authority/<local_authority>/validate')
def validate(local_authority):
    if request.args.get('url') is not None:
        cached = _to_boolean(request.args.get('cached', False))
        url = request.args.get('url').strip()
        try:
            register = BrownfieldSiteRegister.query.get(local_authority)
            register = get_data_and_validate(register, url, cached=cached)
        except FileTypeException as e:
            current_app.logger.exception(e)
            return render_template('not-available.html',
                                   url=url,
                                   local_authority=register,
                                   message=e.message)
        context = {'url': url,
                   'result': register.validation_result,
                   'register': register,
                   }
        if register.validation_result is not None:
            context['feature'] = register.validation_geojson()

        return render_template('result.html', **context)

    return render_template('validate.html', local_authority=local_authority, form=UploadForm())


@frontend.route('/local-authority/<local_authority>/validate-file', methods=['POST'])
def validate_file(local_authority):
    form = UploadForm()
    if form.validate_on_submit():
        f = form.upload.data
        register = BrownfieldSiteRegister.query.get(local_authority)
        _validate_from_file(register, f)
        context = {'url': f.filename,
                   'register': register
                   }
        if register.validation_result is not None:
            context['feature'] = register.validation_geojson()
            if register.validation_has_geo_fixes():
                context['feature_fixed'] = register.validation_geojson(with_fixes=True)

        return render_template('result.html', **context)


@frontend.route('/geojson-download/<local_authority>')
def geojson_download(local_authority):
    register = BrownfieldSiteRegister.query.get(local_authority)
    filename = '%s.geojson' % register.organisation
    return Response(
            json.dumps(register.validation_geojson()),
            mimetype="application/json",
            headers={"Content-disposition":
                     "attachment; filename="+filename})


@frontend.route('/local-authority/<local_authority>/validation-result')
def download_fixed(local_authority):
    register = BrownfieldSiteRegister.query.get(local_authority)
    filename = 'brownfield-register-%s.csv' % register.organisation.replace(':', '-')
    csv_data = register.get_fixed_data().encode('utf-8')
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-disposition': 'attachment; filename=%s' % filename, 'Content-Type': 'text/csv;charset-utf8'})


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
    # publication = BrownfieldSiteValidation.query.get(brownfield_site_publication_id)
    publication = None
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


def _convert_to_csv_if_needed(content, filename, encoding='utf-8'):

    import subprocess
    if _looks_like_csv(content, encoding):
        content = content.decode(encoding)
        return content, len(content.split('\n'))

    with NamedTemporaryFile(delete=False) as f:
        f.write(content)
        file_name = f.name

    csv_file = '%s.csv' % filename

    try:

        if filename.endswith('.xls') or filename.endswith('.xlsx'):
            with open(csv_file, 'wb') as out:
                subprocess.check_call(['in2csv', file_name], stdout=out)

        elif filename.endswith('.xlsm'):
            with open(csv_file, 'wb') as out:
                subprocess.check_call(['xlsx2csv', file_name], stdout=out)

        else:
            msg = 'Not sure how to convert the file %s' % filename
            raise FileTypeException(msg)

        with open(csv_file, 'r') as converted_file:
            content = converted_file.readlines()

        return '\n'.join(content), len(content)

    except Exception as e:
        msg = 'Could not convert %s into csv' % filename
        raise FileTypeException(msg)


def get_data_and_validate(register, url, cached=False):

    if register.validation_result is not None and cached:
        return register
    else:
        file_warnings = []
        resp = requests.get(url)
        content_type = resp.headers.get('Content-type')
        if content_type is not None and content_type.lower() not in ['text/csv', 'text/csv;charset=utf-8']:
            file_warnings.append({'data': 'Content-Type:%s' % content_type, 'warning': ValidationWarning.CONTENT_TYPE_WARNING.to_dict()})

        dammit = UnicodeDammit(resp.content)
        encoding = dammit.original_encoding

        if encoding.lower() != 'utf-8':
            file_warnings.append(
                {'data': 'File encoding: %s' % encoding, 'warning': ValidationWarning.FILE_ENCODING_WARNING.to_dict()})

        content, line_count = _convert_to_csv_if_needed(resp.content, furl(url).path.segments[-1], encoding=encoding)

        validator = BrownfieldSiteValidationRunner(StringInput(string_input=content), file_warnings, line_count, register)
        return validator.validate()


def _validate_from_file(register, file):
    file_warnings = []
    content, line_count = _convert_to_csv_if_needed(file.read(), file.filename)
    validator = BrownfieldSiteValidationRunner(StringInput(string_input=content), file_warnings, line_count, register)
    return validator.validate()


def _looks_like_csv(content, encoding='utf-8'):
    try:
        decoded = content.decode(encoding)
        csv.Sniffer().sniff(decoded)
        return True
    except Exception as e:
        return False

