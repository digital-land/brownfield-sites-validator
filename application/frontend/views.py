import requests
from bs4 import UnicodeDammit

from flask import (
    Blueprint,
    render_template,
    request,
    json)

from application.frontend.forms import BrownfieldSiteURLForm
from application.validators.validators import (
    BrownfieldSiteValidationRunner,
    StringInput,
    ValidationWarning
)

from application.models import BrownfieldSitePublication, Organisation
from application.extensions import db

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/results')
def validate_results():
    publications = BrownfieldSitePublication.query.all()
    return render_template('results.html', publications=publications)


@frontend.route('/start')
def start():
    return render_template('start.html')


@frontend.route('/validate')
def validate():
    form = BrownfieldSiteURLForm(request.args)

    if form.url.data and form.validate():
        if request.args.get('cached') is not None:
            cached = True
        else:
            cached = False
        url = form.url.data.strip()
        result = _get_data_and_validate(url, cached=cached)
        if (result.file_warnings and result.errors) or result.file_errors:
            return render_template('fix.html', url=url, result=result)
        else:
            brownfield_site = BrownfieldSitePublication.query.filter_by(data_url=url).one()
            return render_template('valid.html', url=url, feature=brownfield_site.geojson, result=result)

    return render_template('validate.html', form=form)


@frontend.route('/error')
def error():
    return render_template('not-available.html')


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}


@frontend.context_processor
def asset_path_context_processor():
    return {'assetPath': '/static/govuk-frontend/assets'}


def _get_data_and_validate(url, cached=False):

    # quick hack to use stored validation result. but maybe put timestamp on
    # db record and only use if quite fresh, otherwise fetch and update
    # stored one. Or maybe not do this at all? Just store for index page,
    # but fetch fresh each time validate view method called?
    site = BrownfieldSitePublication.query.filter_by(data_url=url).first()
    if site is not None and site.validation_result is not None and cached:
        return BrownfieldSiteValidationRunner.from_site(site)
    else:
        file_warnings = []
        resp = requests.get(url)
        content_type = resp.headers.get('Content-type')
        if content_type is not None and content_type.lower() not in ['text/csv', 'text/csv;charset=utf-8']:
            file_warnings.append({'data': 'Content-Type:%s' % content_type, 'warning': ValidationWarning.CONTENT_TYPE_WARNING.to_dict()})

        dammit = UnicodeDammit(resp.content)
        encoding = dammit.original_encoding
        if encoding.lower() != 'utf-8':
            file_warnings.append({'data': 'File encoding: %s' % encoding, 'warning': ValidationWarning.FILE_ENCODING_WARNING.to_dict()})

        content = resp.content.decode(encoding)
        line_count = len(content.splitlines())

        publication = BrownfieldSitePublication.query.filter_by(data_url=url).first()
        validator = BrownfieldSiteValidationRunner(StringInput(string_input=content), file_warnings, line_count, publication.organisation)
        validator.validate()

        publication.validation_result = validator.to_dict()
        db.session.add(publication)
        db.session.commit()

        return validator
