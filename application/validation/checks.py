import decimal

from goodtables import Error, check


@check('geox-check', type='custom', context='body')
def geox_check(cells):
    errors = []
    geoX = None
    for cell in cells:
        if cell.get('header') is not None and cell.get('header') == 'GeoX':
            geoX = cell
            break

    if geoX is None:
        return errors

    geoX_value = decimal.Decimal(geoX['value'])

    if geoX_value > 90:
        message = f"GeoX {geoX_value} isn't a longitude using the WGS84 or ETRS89 coordinate systems"
        error = Error(
            'geo-error',
            cell=geoX,
            row_number=cell['row-number'],
            message=message
        )
        errors.append(error)

    if errors:
        return errors

    decimal_places = abs(geoX_value.as_tuple().exponent)
    if decimal_places > 6:
        message = f"GeoY {geoX_value} should not have more than six decimal places"
        error = Error(
            'geo-error',
            cell=geoX,
            row_number=cell['row-number'],
            message=message
        )
        errors.append(error)

    if errors:
        return errors

    if geoX_value < -7 or geoX_value > 2:
        message = f"GeoX (longitude) {geoX_value} is not within the UK"
        error = Error(
            'geo-error',
            cell=geoX,
            row_number=cell['row-number'],
            message=message
        )
        errors.append(error)

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

    geoY_value = decimal.Decimal(geoY['value'])

    if geoY_value > 180:
        message = f"GeoY {geoY_value} isn't a latitude using the WGS84 or ETRS89 coordinate systems"
        error = Error(
            'geo-error',
            cell=geoY,
            row_number=cell['row-number'],
            message=message
        )
        errors.append(error)

    if errors:
        return errors

    decimal_places = abs(geoY_value.as_tuple().exponent)
    if decimal_places > 6:
        message = f"GeoY {geoY_value} should not have more than six decimal places"
        error = Error(
            'geo-error',
            cell=geoY,
            row_number=cell['row-number'],
            message=message
        )
        errors.append(error)

    if errors:
        return errors

    if geoY_value < 49 or geoY_value > 57:
        message = f"GeoY (latitude) {geoY_value} is not within the UK"
        error = Error(
            'geo-error',
            cell=geoY,
            row_number=cell['row-number'],
            message=message
        )
        errors.append(error)

    return errors

