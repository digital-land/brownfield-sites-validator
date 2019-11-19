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

@frontend.route('/validation/<report>/edit/headers', methods=['GET','POST'])
def edit_headers(report):
    report = Report.query.get(report)
    if report is not None:
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


