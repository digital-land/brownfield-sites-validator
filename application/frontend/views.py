import requests
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

    if url.endswith('warning.csv'):
        result = {'warnings': [{'warning': 'encode the file using utf-8'}]}
    elif url.endswith('invalid.csv'):
        result = {'errors': [{'fieldname': 'start date', 'error': 'incorrect date format, use ISO 8601'},
                           {'fieldname': 'location', 'error': 'incorrect co-ordinate system use WGS84'}],
                'warnings': [{'warning': 'encode the file using utf-8'}]}
    else:
        result = {'errors': [], 'warnings': []}

    _check_headers(result, url)

    return result


def _check_headers(result, url):
    resp = requests.head(url)
    content_type = resp.headers.get('Content-type')
    if content_type is not None and content_type != 'text/csv':
        warning = 'Content type is %s Should be set to text/csv' % content_type
        result['warnings'].append(warning)
