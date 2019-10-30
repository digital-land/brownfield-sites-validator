import os
import tempfile
import goodtables

from werkzeug.utils import secure_filename

from application.utils import (
    convert_to_csv_if_needed,
    original_brownfield_register_fields
)

from application.validation.schema import brownfield_site_schema

updated_brownfield_register_fields = [item['name'] for item in brownfield_site_schema['fields']]


def handle_file_and_check(upload_data):
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = f'{temp_dir}/data'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        filename = secure_filename(upload_data.filename)
        file = os.path.join(output_dir, filename)
        upload_data.save(file)
        try:
            file, file_type = convert_to_csv_if_needed(file)
            data, additional_fields = process_csv_file(file)
            results = check(data)
            # TODO make a report from validation result. Start with
            # listing fields from file that aren't needed
            # Then also list fields that may have had to be renamed to validate
            # lastly compile a report from these results
            results['additional-fields'] = additional_fields

        except Exception as e:
            print(e)
            results = {'error': str(e)}
    return results


def process_csv_file(csv_file):
    import pandas as pd
    df = pd.read_csv(csv_file, na_filter= False, encoding='ISO-8859-1')

    # TODO fixup column names

    columns_to_ignore = set(original_brownfield_register_fields) - set(updated_brownfield_register_fields)
    additional_columns = set(df.columns) - set(updated_brownfield_register_fields)
    df.drop(columns_to_ignore, axis=1, inplace=True)
    return df.to_dict(orient='records'), list(additional_columns)


def check(data):
    return goodtables.validate(data, schema=brownfield_site_schema, order_fields=True)