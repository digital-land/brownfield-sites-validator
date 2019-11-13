from flask import (
    Blueprint,
    render_template,
    jsonify,
    flash,
    url_for,
    abort
)
from werkzeug.utils import secure_filename, redirect

from application.extensions import db
from application.frontend.forms import UploadForm
from application.validation.reporter import Report
from application.validation.utils import FileTypeException, BrownfieldStandard
from application.validation.validator import handle_upload_and_validate

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/validate', methods=['GET','POST'])
def validate():
    form = UploadForm()
    if form.validate_on_submit():
        try:
            filename = secure_filename(form.upload.data.filename)
            data = form.upload.data
            report = handle_upload_and_validate(data, filename)
            db.session.add(report)
            db.session.commit()
            return redirect(url_for('frontend.validation_report', report=report.id))
        except FileTypeException as e:
            flash(f'{e}', category='error')

    return render_template('upload.html', form=form)


@frontend.route('/validation/<report>')
def validation_report(report):
    report = Report.query.get(report)
    if report is not None:
        return render_template('validation-result.html',
                               report=report,
                               brownfield_standard=BrownfieldStandard)
    abort(404)


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


