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
    ValidationWarning
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
        if request.args.get('cached') is not None:
            cached = True
        else:
            cached = False
        result = _get_data_and_validate(form.url.data, cached=cached)
        if (result.file_warnings and result.errors) or result.file_errors:
            return render_template('fix.html', url=form.url.data, result=result)
        else:
            brownfield_site = BrownfieldSitePublication.query.filter_by(data_url=form.url.data).one()
            return render_template('valid.html', url=form.url.data, feature=brownfield_site.geojson, result=result)

    return render_template('validate.html', form=form)


@frontend.route('/validate/results')
def validate_results():
    sites = BrownfieldSitePublication.query.filter(BrownfieldSitePublication.validation_result.isnot(None))
    return render_template('results.html', sites=sites)


@frontend.route('/error')
def error():
    return render_template('not-available.html')


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}


def _get_data_and_validate(url, cached=False):

    # quick hack to use stored validation result. but maybe put timestamp on
    # db record and only use if quite fresh, otherwise fetch and update
    # stored one. Or maybe not do this at all? Just store for index page,
    # but fetch fresh each time validate view method called?
    site_in_db = BrownfieldSitePublication.query.filter_by(data_url=url).first()
    if site_in_db is not None and site_in_db.validation_result is not None and cached:
        return BrownfieldSiteValidator.from_dict(site_in_db.validation_result)
    else:
        file_warnings = []
        resp = requests.get(url)
        content_type = resp.headers.get('Content-type')
        if content_type is not None and content_type != 'text/csv':
            file_warnings.append({'data': 'Content-Type:%s' % content_type, 'warning': ValidationWarning.CONTENT_TYPE_WARNING.to_dict()})

        dammit = UnicodeDammit(resp.content)
        encoding = dammit.original_encoding
        if encoding != 'utf-8':
            file_warnings.append({'data': 'File encoding: %s' % encoding, 'warning': ValidationWarning.FILE_ENCODING_WARNING.to_dict()})

        content = resp.content.decode(encoding)
        line_count = len(content.splitlines())

        validator = BrownfieldSiteValidator(source=StringInput(string_input=content), file_warnings=file_warnings, line_count=line_count)
        return validator.validate()
