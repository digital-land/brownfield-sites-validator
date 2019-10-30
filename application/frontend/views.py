from flask import (
    Blueprint,
    render_template,
    jsonify
)

from application.frontend.forms import UploadForm
from application.utils import ordered_brownfield_register_fields, temp_fields_seen_in_register
from application.validation.validator import handle_file_and_check

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/upload', methods=['GET','POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        results = handle_file_and_check(form.upload.data)
        return results
    return render_template('upload.html', form=form)


@frontend.route('/validation-result')
def validation_result():
    render_template('validation-result.html', expected=ordered_brownfield_register_fields, seen=temp_fields_seen_in_register)


@frontend.route('/schema')
def schema():
    from application.validation.schema import brownfield_site_schema
    return jsonify(brownfield_site_schema)


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}


@frontend.context_processor
def assetPath_context_processor():
    return {'assetPath': '/static/govuk-frontend/assets'}


