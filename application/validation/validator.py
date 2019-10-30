import os
import tempfile
import goodtables

from werkzeug.utils import secure_filename

from application.utils import convert_to_csv_if_needed
from application.validation.schema import brownfield_site_schema


def handle_file_and_check(upload_data):
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = f'{temp_dir}/data'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        filename = secure_filename(upload_data.filename)
        file = os.path.join(output_dir, filename)
        upload_data.save(file)
        try:
            file = convert_to_csv_if_needed(file)
            results = check(file)
        except Exception as e:
            print(e)
            results = {'error': str(e)}
    return results


def check(file):
    return goodtables.validate(file, schema=brownfield_site_schema, order_fields=True)


