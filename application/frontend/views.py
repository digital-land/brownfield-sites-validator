import requests
from bs4 import UnicodeDammit

from flask import (
    Blueprint,
    render_template,
    request,
    json)
from sqlalchemy import asc

from application.frontend.forms import BrownfieldSiteURLForm
from application.validators.validators import (
    BrownfieldSiteValidationRunner,
    StringInput,
    ValidationWarning
)

from application.models import BrownfieldSitePublication, Organisation, ValidationResult
from application.extensions import db

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/results')
def validate_results():
    publications = BrownfieldSitePublication.query.join(Organisation).order_by(asc(Organisation.name))
    return render_template('results.html', publications=publications)


@frontend.route('/start')
def start():
    return render_template('start.html')


def _to_boolean(value):
    if str(value).lower() in ['1', 't', 'true', 'y', 'yes', 'on']:
        return True
    return False


@frontend.route('/validate')
def validate():
    form = BrownfieldSiteURLForm(request.args)

    if form.url.data and form.validate():

        cached = _to_boolean(request.args.get('cached', False))

        url = form.url.data.strip()
        result = _get_data_and_validate(url, cached=cached)
        if (result.file_warnings and result.errors) or result.file_errors:
            return render_template('fix.html', url=url, result=result)
        else:
            brownfield_site = BrownfieldSitePublication.query.filter_by(data_url=url).one()
            la_boundary=brownfield_site.organisation.feature.geojson

            return render_template('valid.html',
                                   url=url,
                                   feature=brownfield_site.geojson,
                                   result=result,
                                   la_boundary=la_boundary)

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
    publication = BrownfieldSitePublication.query.filter_by(data_url=url).first()
    if publication is not None and publication.validation is not None and cached:
        return BrownfieldSiteValidationRunner.from_publication(publication)
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
        validator = BrownfieldSiteValidationRunner(StringInput(string_input=content), file_warnings, line_count, publication)
        return validator.validate()
