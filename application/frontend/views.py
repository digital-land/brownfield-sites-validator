import collections
import csv
import io
import os
import tempfile

from flask import (
    Blueprint,
    render_template,
    jsonify,
    flash,
    url_for,
    abort,
    request,
    make_response
)

from werkzeug.utils import secure_filename, redirect
from application.extensions import db
from application.frontend.forms import UploadForm
from application.frontend.models import ResultModel
from application.validation.validation_result import Result
from application.validation.utils import FileTypeException, BrownfieldStandard
from application.validation.validator import validate_file, revalidate_result

frontend = Blueprint('frontend', __name__, template_folder='templates')

Edit = collections.namedtuple('Edit', 'index current update')


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/validate', methods=['GET', 'POST'])
def validate():
    form = UploadForm()
    if form.validate_on_submit():
        try:
            res = _write_tempfile_and_validate(form)
            result = ResultModel(res)
            db.session.add(result)
            db.session.commit()
            return redirect(url_for('frontend.validation_result', result=result.id))
        except FileTypeException as e:
            flash(f'{e}', category='error')

    return render_template('upload.html', form=form)


@frontend.route('/validation/<result>')
def validation_result(result):
    db_result = ResultModel.query.get(result)
    if db_result is not None:
        result = Result(**db_result.to_dict())
        return render_template('validation-result.html',
                               result=result,
                               brownfield_standard=BrownfieldStandard)
    abort(404)


@frontend.route('/schema')
def schema():
    return jsonify(BrownfieldStandard.v2_standard_schema())


@frontend.route('/validation/<result>/edit/headers', methods=['GET', 'POST'])
def edit_headers(result):
    db_result = ResultModel.query.get(result)
    if db_result is not None:
        result = Result(**db_result.to_dict())
        if request.method == 'POST':
            original_additional_headers = sorted(result.extra_headers_found(), key=lambda v: (v.upper(), v[0].islower()))
            try:
                header_edits, new_headers = compile_header_edits(request.form, original_additional_headers)
            except InvalidEditException as e:
                return render_template('edit-headers.html',
                                       result=result,
                                       brownfield_standard=BrownfieldStandard,
                                       invalid_edits=e.invalid_edits)
            result, updated_headers, removed_headers = update_and_save_headers(result, header_edits, new_headers)
            result = revalidate_result(result)
            db_result.update(result)
            db.session.add(db_result)
            db.session.commit()
            return render_template('edit-confirmation.html',
                                   result=result,
                                   updated_headers=updated_headers,
                                   removed_headers=removed_headers)

    return render_template('edit-headers.html',
                           result=result,
                           brownfield_standard=BrownfieldStandard)


@frontend.route('/validation/<result>/csv')
def get_csv(result):
    result_model = ResultModel.query.get(result)
    if result_model is not None:
        result = Result(**result_model.to_dict())
        fields = BrownfieldStandard.v2_standard_headers()
        # TODO append deprecated headers and get data for these from original upload
        output = io.StringIO()
        writer = csv.DictWriter(output, fields)
        writer.writeheader()
        for r in result.rows:
            writer.writerow(r)
        csv_output = output.getvalue().encode('utf-8')
        response = make_response(csv_output)
        response.headers['Content-Disposition'] = f'attachment; filename=brownfield-land.csv'
        response.headers['Content-Type'] = 'text/csv'
        return response
    else:
        abort(404)


@frontend.route('/validation/edit/success')
def edit_complete():
    return render_template('edit-success.html')


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}


@frontend.context_processor
def assetPath_context_processor():
    return {'assetPath': '/static/govuk-frontend/assets'}


class InvalidEditException(Exception):

    def __init__(self, message, invalid_edits):
        super().__init__(message)
        self.invalid_edits = invalid_edits


def compile_header_edits(form, originals):
    header_edits = []
    new_headers = []
    invalid_edits = {}
    for i in form:
        if "update-header" in i:
            header_idx = int(i.split("-")[2])
            edit = Edit(index=header_idx, current=originals[header_idx], update=form[i])
            header_edits.append(edit)
        else:
            new_headers.append(form[i])

    for edit in header_edits:
        if edit.current != edit.update and edit.update not in BrownfieldStandard.v2_standard_headers():
            invalid_edits[edit.index] = edit
    if invalid_edits:
        raise InvalidEditException('Some headers were updated to invalid values', invalid_edits)
    return header_edits, new_headers


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


def set_new_header(result, current, update):
    for i, row in enumerate(result.upload):
        item = row.pop(current, None)
        if item is not None:
            result.rows[i][update] = item


def add_new_header(result, header):
    for i, row in enumerate(result.rows):
        result.rows[i][header] = ''


def update_and_save_headers(result, header_edits, new_headers):
    headers_added = []
    headers_removed = []
    for edit in header_edits:
        if edit.current != edit.update:
            set_new_header(result, current=edit.current, update=edit.update)
            headers_added.append(edit.update)
            headers_removed.append(edit.current)
        else:
            headers_removed.append(edit.current)

    for header in new_headers:
        if header not in headers_added:
            add_new_header(result, header)
            headers_added.append(header)

    result.reconcile_header_results(headers_added=headers_added,
                                    headers_removed=headers_removed)

    return result, headers_added, headers_removed
