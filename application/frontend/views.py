import csv
import requests

from tempfile import NamedTemporaryFile
from bs4 import UnicodeDammit

from flask import (
    Blueprint,
    render_template,
)

from furl import furl
from application.frontend.forms import UploadForm
from application.utils import to_boolean

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/upload', methods=['GET','POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        return 'OK'
    return render_template('upload.html', form=form)


@frontend.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template'}


@frontend.context_processor
def assetPath_context_processor():
    return {'assetPath': '/static/govuk-frontend/assets'}


class FileTypeException(Exception):

    def __init__(self, message):
        self.message = message


# def _convert_to_csv_if_needed(content, filename, encoding='utf-8'):
#
#     import subprocess
#     if _looks_like_csv(content, encoding):
#         content = content.decode(encoding)
#         return content, len(content.split('\n'))
#
#     with NamedTemporaryFile(delete=False) as f:
#         f.write(content)
#         file_name = f.name
#
#     csv_file = '%s.csv' % filename
#
#     try:
#
#         if filename.endswith('.xls') or filename.endswith('.xlsx'):
#             with open(csv_file, 'wb') as out:
#                 subprocess.check_call(['in2csv', file_name], stdout=out)
#
#         elif filename.endswith('.xlsm'):
#             with open(csv_file, 'wb') as out:
#                 subprocess.check_call(['xlsx2csv', file_name], stdout=out)
#
#         else:
#             msg = 'Not sure how to convert the file %s' % filename
#             raise FileTypeException(msg)
#
#         with open(csv_file, 'r') as converted_file:
#             content = converted_file.readlines()
#
#         return '\n'.join(content), len(content)
#
#     except Exception as e:
#         msg = 'Could not convert %s into csv' % filename
#         raise FileTypeException(msg)


# def get_data_and_validate(register, url, cached=False):
#
#     if register.validation_result is not None and cached:
#         return register
#     else:
#         file_warnings = []
#         resp = requests.get(url)
#         content_type = resp.headers.get('Content-type')
#         if content_type is not None and content_type.lower() not in ['text/csv', 'text/csv;charset=utf-8']:
#             file_warnings.append({'data': 'Content-Type:%s' % content_type, 'warning': ValidationWarning.CONTENT_TYPE_WARNING.to_dict()})
#
#         dammit = UnicodeDammit(resp.content)
#         encoding = dammit.original_encoding
#
#         if encoding.lower() != 'utf-8':
#             file_warnings.append(
#                 {'data': 'File encoding: %s' % encoding, 'warning': ValidationWarning.FILE_ENCODING_WARNING.to_dict()})
#
#         content, line_count = _convert_to_csv_if_needed(resp.content, furl(url).path.segments[-1], encoding=encoding)
#
#         validator = BrownfieldSiteValidationRunner(StringInput(string_input=content), file_warnings, line_count, register)
#         return validator.validate()
#
#
# def _validate_from_file(register, file):
#     file_warnings = []
#     content, line_count = _convert_to_csv_if_needed(file.read(), file.filename)
#     validator = BrownfieldSiteValidationRunner(StringInput(string_input=content), file_warnings, line_count, register)
#     return validator.validate()
#
#
# def _looks_like_csv(content, encoding='utf-8'):
#     try:
#         decoded = content.decode(encoding)
#         csv.Sniffer().sniff(decoded)
#         return True
#     except Exception as e:
#         return False

