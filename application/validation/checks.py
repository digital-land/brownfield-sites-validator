import logging

from goodtables import Error, check
from validators import url
from validator.utils import logging_handler

LATITUDE = 'latitude'
LONGITUDE = 'longitude'
MINIMUM_UK_LATITUDE = 49
MAXIMUM_UK_LATITUDE = 57
MINIMUM_UK_LONGITUDE = -7
MAXIMUM_UK_LONGITUDE = 2
MAX_DECIMAL_PLACES = 6


logger = logging.getLogger(__name__)
logger.addHandler(logging_handler)


@check('geox-check', type='custom', context='body')
def geox_check(cells):
    errors = []
    geoX = _get_field(cells, 'GeoX')
    if geoX is None:
        return errors

    errors += _check_looks_like_correct_coordinate_ref_system(geoX, 180, '%s' % LONGITUDE)

    if errors:
        return errors

    errors += _check_decimal_places(geoX, MAX_DECIMAL_PLACES)

    if errors:
        return errors

    errors += _check_lat_long_in_range(geoX, MINIMUM_UK_LONGITUDE, MINIMUM_UK_LONGITUDE, LONGITUDE)

    return errors


@check('geoy-check', type='custom', context='body')
def geoy_check(cells):
    errors = []
    geoY = None
    for cell in cells:
        if cell.get('header') is not None and cell.get('header') == 'GeoY':
            geoY = cell
            break

    if geoY is None:
        return errors

    errors += _check_looks_like_correct_coordinate_ref_system(geoY, 90, '%s' % LATITUDE)

    if errors:
        return errors

    errors += _check_decimal_places(geoY, MAX_DECIMAL_PLACES)

    if errors:
        return errors

    errors += _check_lat_long_in_range(geoY, MINIMUM_UK_LATITUDE, MAXIMUM_UK_LATITUDE, LATITUDE)

    return errors


def _get_field(cells, field_name):
    field = None
    for cell in cells:
        if cell.get('header') is not None and cell.get('header') == field_name:
            field = cell
            break
    return field


def _check_looks_like_correct_coordinate_ref_system(field, max_value, lat_or_long):
    errors = []
    if abs(field['value']) > max_value:
        message = f"{field['value']} isn't a {lat_or_long} using the WGS84 or ETRS89 coordinate systems"
        error = Error(
            'geo-error',
            cell=field,
            row_number=field['row-number'],
            message=message,
            message_substitutions={
                'value': f"{field['value']}"
            }
        )
        errors.append(error)
    return errors


def _check_decimal_places(field, max_decimal_places):
    errors = []
    decimal_places = abs(field['value'].as_tuple().exponent)
    if decimal_places > max_decimal_places:
        message = f"{field['value']} should not have more than six decimal places"
        error = Error(
            'geo-error',
            cell=field,
            row_number=field['row-number'],
            message=message,
            message_substitutions={
                'value': f"{field['value']}"
            }
        )
        errors.append(error)
    return errors


def _check_lat_long_in_range(field, minimum, maximum, axis):
    errors = []
    if not minimum < field['value'] < maximum:
        message = f"{field['value']} is not a {axis} within the UK"
        error = Error(
            'geo-error',
            cell=field,
            row_number=field['row-number'],
            message=message,
            message_substitutions={
                'value': f"{field['value']}"
            }
        )
        errors.append(error)
    return errors


@check('url-list-check', type='custom', context='body')
def url_list_check(cells):
    errors = []
    try:
        field = _get_field(cells, 'PlanningHistory')
        if field is None:
            return errors
        else:
            urls = field['value'].split('|')
            for u in urls:
                is_valid = url(u.strip())
                if not is_valid:
                    message = f'{u.strip()} is not a url'
                    error = Error(
                        'url-list-error',
                        cell=field,
                        row_number=field['row-number'],
                        message=message,
                        message_substitutions={
                            'value': f"{field['value'].strip()}"
                        }
                    )
                    errors.append(error)
    except Exception as e:  # noqa
        logger.exception(f'error with {field}')
    return errors
