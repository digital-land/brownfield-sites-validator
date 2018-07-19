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
        warnings, errors, missing = _get_data_and_validate(form.url.data)
        if warnings or errors:
            return render_template('fix.html', url=form.url.data, warnings=warnings, errors=errors, missing=missing)
        else:
            from application.data.stubs import geojson
            return render_template('valid.html', url=form.url.data, geojson=geojson)
    return render_template('validate.html', form=form)


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

    validator = BrownfieldSiteRegisterValidator(source=String(string_input=resp.content.decode(encoding)),
                                                ignore_missing_validators=True)
    validator.validate()

    # unpack the validator error messages from the exception class until we come up with something tidy?
    errors = []
    for field, failure in validator.failures.items():
        unpacked = []
        for line_no, errs in failure.items():
            unpacked.append({line_no: [message.args[0] for message in errs]})
        errors.append({field: unpacked})

    missing = []
    for f in validator.missing_fields:
        missing.append(f)

    return warnings, errors, missing


