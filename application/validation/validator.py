import logging
import goodtables

from goodtables import check
from application.validation.utils import extract_data, FileTypeException, BrownfieldStandard
from application.validation.reporter import Report
brownfield_standard_v2_schema = BrownfieldStandard.v2_standard_schema()

custom_checks=['geox-check','geoy-check', 'url-list-check']  # TODO the list of checks could be config or cli options?
builtin_checks = ['structure', 'schema']
checks = builtin_checks + custom_checks


def validate_file(file, schema=brownfield_standard_v2_schema):
    try:
        extracted_data = extract_data(file)
        result = check(extracted_data, schema)
        original_data = extracted_data.pop('original_data')
        validated_data = extracted_data.pop('validated_data')
        return Report(raw_result=result,
                      original_data=original_data,
                      validated_data=validated_data,
                      additional_data=extracted_data)
    except FileTypeException as e:
        logging.exception(e)
        raise e


def check(data, schema):
    rows = data.get('validated_data')
    return goodtables.validate(rows, schema=schema, order_fields=True, checks=checks)
