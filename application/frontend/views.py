import requests
from bs4 import UnicodeDammit

from flask import (
    Blueprint,
    render_template,
    request
)

from application.frontend.forms import BrownfieldSiteURLForm
from application.validators.validators import (
    BrownfieldSiteValidator,
    StringInput,
    Warning
)

from application.models import BrownfieldSitePublication

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/validate')
def validate():
    form = BrownfieldSiteURLForm(request.args)

    if form.url.data and form.validate():
        result = _get_data_and_validate(form.url.data)
        if (result.file_warnings and result.errors) or result.file_errors:
            return render_template('fix.html', url=form.url.data, result=result)
        else:
            brownfield_site = BrownfieldSitePublication.query.filter_by(data_url=form.url.data).one()
            return render_template('valid.html', url=form.url.data, feature=brownfield_site.geojson, result=result)

    return render_template('validate.html', form=form)


@frontend.route('/validate/results')
def validate_results():
    import json
    sites = BrownfieldSitePublication.query.filter(BrownfieldSitePublication.validation_result.isnot(None))
    return render_template('results.html', sites=sites)


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
        file_warnings.append({'data': 'Content-Type:%s' % content_type, 'warning': Warning.CONTENT_TYPE_WARNING.to_dict()})

    dammit = UnicodeDammit(resp.content)
    encoding = dammit.original_encoding
    if encoding != 'utf-8':
        file_warnings.append({'data': 'File encoding: %s' % encoding, 'warning': Warning.FILE_ENCODING_WARNING.to_dict()})

    content = resp.content.decode(encoding)
    line_count = len(content.splitlines())

    validator = BrownfieldSiteValidator(source=StringInput(string_input=content), file_warnings=file_warnings, line_count=line_count)
    return validator.validate()
