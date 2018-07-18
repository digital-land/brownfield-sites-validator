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

from vladiate.inputs import String
from application.frontend.forms import BrownfieldSiteURLForm
from application.frontend.validators import ValidatorWarning, BrownfieldSiteRegisterValidator


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


