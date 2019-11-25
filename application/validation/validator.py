import logging
import goodtables

from application.validation.utils import extract_data, FileTypeException, BrownfieldStandard
from application.validation.validation_result import Result
brownfield_standard_v2_schema = BrownfieldStandard.v2_standard_schema()

custom_checks = ['geox-check', 'geoy-check', 'url-list-check']  # TODO the list of checks could be config or cli options?
builtin_checks = ['structure', 'schema']
checks = builtin_checks + custom_checks


def validate_file(file, schema=brownfield_standard_v2_schema):
    try:
        extracted = extract_data(file)

        data = extracted.get('data')
        rows = extracted.get('rows')
        meta_data = extracted.get('meta_data')

        result = check_data(rows, schema)

        return Result(result=result,
                      upload=data,
                      rows=rows,
                      meta_data=meta_data)

    except FileTypeException as e:
        logging.exception(e)
        raise e


def check_data(data, schema):
    return goodtables.validate(data, schema=schema, order_fields=True, checks=checks)


def revalidate_result(result, schema=brownfield_standard_v2_schema):
    res = check_data(result.rows, schema)
    return Result(id=result.id,
                  result=res,
                  upload=result.upload,
                  rows=result.rows,
                  meta_data=result.meta_data)
