import os
import tempfile
import collections

from validator.standards import BrownfieldStandard
from werkzeug.utils import secure_filename
from validator.validation_result import Result
from validator.validator import validate_file, check_data


brownfield_standard = BrownfieldStandard()


class InvalidEditException(Exception):

    def __init__(self, message, invalid_edits):
        super().__init__(message)
        self.invalid_edits = invalid_edits


Edit = collections.namedtuple('Edit', 'index current update')


def to_boolean(value):
    if value is None:
        return False
    if str(value).lower() in ['1', 't', 'true', 'y', 'yes', 'on']:
        return True
    return False


def compile_header_edits(form, originals):
    header_edits = []
    new_headers = []
    invalid_edits = {}
    if originals:
        for i in form:
            if "update-header" in i:
                header_idx = int(i.split("-")[2])
                edit = Edit(index=header_idx, current=originals[header_idx], update=form[i])
                header_edits.append(edit)
            else:
                new_headers.append(form[i])

        for edit in header_edits:
            if edit.current != edit.update and edit.update not in brownfield_standard.current_standard_headers():
                invalid_edits[edit.index] = edit
        if invalid_edits:
            raise InvalidEditException('Some headers were updated to invalid values', invalid_edits)
    return header_edits, new_headers


def write_tempfile_and_validate(form):
    with tempfile.TemporaryDirectory() as temp_dir:
        filename = secure_filename(form.upload.data.filename)
        output_dir = f'{temp_dir}/data'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        file = os.path.join(output_dir, filename)
        form.upload.data.save(file)
        report = validate_file(file, brownfield_standard)
    return report


def set_new_header(result, current, update):
    for i, row in enumerate(result.input):
        item = row.pop(current, None)
        if item is not None:
            result.rows[i][update] = item


def add_new_header(result, header):
    for i, row in enumerate(result.rows):
        result.rows[i][header] = ''


def update_and_save_headers(result, header_edits, new_headers):
    headers_added = []
    headers_removed = []
    header_changes = []
    for edit in header_edits:
        if edit.current != edit.update:
            set_new_header(result, current=edit.current, update=edit.update)
            headers_added.append(edit.update)
            headers_removed.append(edit.current)
            header_changes.append((edit.update, edit.current))
        else:
            headers_removed.append(edit.current)

    for header in new_headers:
        if header not in headers_added:
            add_new_header(result, header)
            headers_added.append(header)
            header_changes.append((header, "ADDED"))

    result.reconcile_header_results(headers_added=headers_added,
                                    headers_removed=headers_removed)

    return {'result': result,
            'headers_added': headers_added,
            'headers_removed': headers_removed,
            'header_changes': header_changes}


def revalidate_result(result, standard):
    res = check_data(result.rows, standard.schema)
    return Result(id=result.id,
                  result=res,
                  input=result.input,
                  rows=result.rows,
                  meta_data=result.meta_data,
                  standard=standard)