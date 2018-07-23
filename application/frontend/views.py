import requests
from bs4 import UnicodeDammit

from flask import (
    Blueprint,
    render_template,
    request
)

from application.frontend.forms import BrownfieldSiteURLForm
from application.frontend.validators import BrownfieldSiteValidator, StringInput, Warning, ValidationIssue

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/validate')
def validate():
    form = BrownfieldSiteURLForm(request.args)

    if form.url.data and form.validate():
        result = _get_data_and_validate(form.url.data)
        if result.file_warnings and result.errors:
            return render_template('fix.html', url=form.url.data, result=result)
        else:
            from application.data.stubs import geojson
            return render_template('valid.html', url=form.url.data, geojson=geojson, result=result)

    return render_template('validate.html', form=form)


@frontend.route('/error')
def error():
    return render_template('not-available.html')


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}


def _get_data_and_validate(url):

    file_warnings = []

    resp = requests.get(url)
    content_type = resp.headers.get('Content-type')
    if content_type is not None and content_type != 'text/csv':
        file_warnings.append(ValidationIssue('Content-Type:%s' % content_type, Warning.CONTENT_TYPE_WARNING))

    dammit = UnicodeDammit(resp.content)
    encoding = dammit.original_encoding
    if encoding != 'utf-8':
        file_warnings.append(ValidationIssue('File encoding: %s' % encoding, Warning.FILE_ENCODING_WARNING))

    content = resp.content.decode(encoding)
    line_count = len(content.splitlines())

    validator = BrownfieldSiteValidator(source=StringInput(string_input=content), file_warnings=file_warnings, line_count=line_count)
    return validator.validate()
