import csv
import io

from flask import (
    Blueprint,
    render_template,
    jsonify,
    flash,
    url_for,
    abort,
    request,
    make_response,
)
from validator.standards import BrownfieldStandard
from validator.utils import FileTypeException
from validator.validation_result import Result
from werkzeug.utils import redirect

from application.extensions import db
from application.frontend.forms import UploadForm
from application.frontend.models import ResultModel
from application.utils import (
    InvalidEditException,
    compile_header_edits,
    write_tempfile_and_validate,
    update_and_save_headers,
    revalidate_result,
)

brownfield_standard = BrownfieldStandard()

frontend = Blueprint("frontend", __name__, template_folder="templates")


@frontend.route("/")
def index():
    return render_template("index.html")


@frontend.route("/validate", methods=["GET", "POST"])
def validate():
    form = UploadForm()
    if form.validate_on_submit():
        try:
            res = write_tempfile_and_validate(form)
            result = ResultModel(res)
            db.session.add(result)
            db.session.commit()
            return redirect(url_for("frontend.validation_result", result=result.id))
        except FileTypeException as e:
            flash(f"{e}", category="error")

    return render_template("upload.html", form=form)


@frontend.route("/validation/<result>")
def validation_result(result):
    db_result = ResultModel.query.get(result)
    if db_result is not None:
        result = Result(**db_result.to_dict(), standard=brownfield_standard)
        updated_at = db_result.updated_at
        return render_template(
            "validation-result.html", result=result, register_updated_at=updated_at
        )
    abort(404)


@frontend.route("/schema")
def schema():
    return jsonify(brownfield_standard.current_standard_headers())


@frontend.route("/validation/<result>/edit/headers", methods=["GET", "POST"])
def edit_headers(result):
    db_result = ResultModel.query.get(result)
    if db_result is not None:
        result = Result(**db_result.to_dict(), standard=brownfield_standard)
        if request.method == "POST":
            original_additional_headers = sorted(
                result.extra_headers_found(), key=lambda v: (v.upper(), v[0].islower())
            )
            try:
                header_edits, new_headers = compile_header_edits(
                    request.form, original_additional_headers
                )
            except InvalidEditException as e:
                return render_template(
                    "edit-headers.html", result=result, invalid_edits=e.invalid_edits
                )
            update = update_and_save_headers(result, header_edits, new_headers)
            result = revalidate_result(result, brownfield_standard)
            db_result.update(result)
            db.session.add(db_result)
            db.session.commit()
            return render_template(
                "edit-confirmation.html",
                result=update["result"],
                updated_headers=update["headers_added"],
                removed_headers=update["headers_removed"],
                header_changes=update["header_changes"],
            )

    return render_template("edit-headers.html", result=result)


@frontend.route("/validation/<result>/edit/column/<column>")
def edit_column(result, column):
    db_result = ResultModel.query.get(result)
    if db_result is not None:
        result = Result(**db_result.to_dict(), standard=brownfield_standard)
        if "Date" not in column or result.errors_by_column.get(column) is None:
            # colm, if they get the page again there will be not errors_by_column for this
            # column if we've re-validated
            return render_template(
                "edit-column-confirmation.html", column=column, result=result
            )

        fixes_applied = result.apply_fixes(column)
        result = revalidate_result(result, brownfield_standard)
        db_result.update(result)
        db.session.add(db_result)
        db.session.commit()
        return render_template(
            "edit-column-confirmation.html",
            column=column,
            result=result,
            fixes_applied=fixes_applied,
            edited=True,
        )


@frontend.route("/validation/<result>/csv")
def get_csv(result):
    result_model = ResultModel.query.get(result)
    if result_model is not None:
        result = Result(**result_model.to_dict(), standard=brownfield_standard)
        fields = brownfield_standard.current_standard_headers()
        deprecated = result.meta_data["additional_headers"]
        fields.extend(deprecated)
        output = io.StringIO()
        writer = csv.DictWriter(output, fields)
        writer.writeheader()
        for i, row in enumerate(result.rows):
            r = row
            original = result.input[i]
            for field in deprecated:
                r[field] = original.get(field, "")
            writer.writerow(r)
        csv_output = output.getvalue().encode("utf-8")
        response = make_response(csv_output)
        response.headers[
            "Content-Disposition"
        ] = f"attachment; filename=brownfield-land.csv"
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        return response
    else:
        abort(404)


@frontend.route("/validation/edit/success")
def edit_complete():
    return render_template("edit-success.html")


@frontend.context_processor
def asset_path_context_processor():
    return {"asset_path": "/static/govuk_template"}


@frontend.context_processor
def assetPath_context_processor():
    return {"assetPath": "/static/govuk-frontend/assets"}
