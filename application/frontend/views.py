import os
import tempfile

from flask import (
    Blueprint,
    render_template,
    jsonify,
    flash,
    url_for,
    abort,
    request
)

from werkzeug.utils import secure_filename, redirect
from application.extensions import db
from application.frontend.forms import UploadForm
from application.frontend.models import ValidationReport
from application.validation.reporter import Report
from application.validation.utils import FileTypeException, BrownfieldStandard
from application.validation.validator import validate_file

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/validate', methods=['GET', 'POST'])
def validate():
    form = UploadForm()
    if form.validate_on_submit():
        try:
            report = _write_tempfile_and_validate(form)
            validation_report = ValidationReport(report)
            db.session.add(validation_report)
            db.session.commit()
            return redirect(url_for('frontend.validation_report', report=validation_report.id))
        except FileTypeException as e:
            flash(f'{e}', category='error')

    return render_template('upload.html', form=form)


@frontend.route('/validation/<report>')
def validation_report(report):
    validation_report = ValidationReport.query.get(report)
    if validation_report is not None:
        report = Report(**validation_report.to_dict())
        return render_template('validation-result.html',
                               report=report,
                               brownfield_standard=BrownfieldStandard)
    abort(404)


@frontend.route('/schema')
def schema():
    return jsonify(BrownfieldStandard.v2_standard_schema())


def _write_tempfile_and_validate(form):
    with tempfile.TemporaryDirectory() as temp_dir:
        filename = secure_filename(form.upload.data.filename)
        output_dir = f'{temp_dir}/data'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        file = os.path.join(output_dir, filename)
        form.upload.data.save(file)
        report = validate_file(file)
    return report


# returns tuple list of header edits
# e.g. ('SitePlanURL', 'SiteplanURL')
def compile_header_edits(form, originals):
    header_edits = []
    new_headers = []
    for i in form:
        if "update-header" in i:
            header_idx = int(i.split("-")[2]) - 1
            header_edits.append((originals[header_idx], form[i]))
        else:
            new_headers.append(form[i])
    return header_edits, new_headers


@frontend.route('/validation/<report>/edit/headers', methods=['GET', 'POST'])
def edit_headers(report):
    validation_report = ValidationReport.query.get(report)
    if validation_report is not None:
        report = Report(**validation_report.to_dict())
        if request.method == 'POST':
            original_additional_headers = sorted(report.extra_headers_found(), key=lambda v: (v.upper(), v[0].islower()))
            header_edits, new_headers = compile_header_edits(request.form, original_additional_headers)
            for header in header_edits:
                if header[0] is not header[1]:
                    print('Need to save the edited header: ' + header[0] + " now " + header[1])
            # To do
            # need to make the changes to csv file
            # - update edited headers first
            # - then add any remaining ticked headers if that header doesn't exist
            print("Need to create: ", new_headers)
        return render_template('edit-headers.html',
                               report=report,
                               brownfield_standard=BrownfieldStandard)


@frontend.route('/validation/edit/success')
def edit_complete():
    return render_template('edit-success.html')


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}


@frontend.context_processor
def assetPath_context_processor():
    return {'assetPath': '/static/govuk-frontend/assets'}
