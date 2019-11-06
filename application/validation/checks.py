from goodtables import Error, check

MAX_DECIMAL_PLACES = 6


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

    if abs(geoX['value']) > 180:
        message = f"{geoX['value']} isn't a longitude using the WGS84 or ETRS89 coordinate systems"
        error = Error(
            'geo-error',
            cell=geoX,
            row_number=cell['row-number'],
            message=message
        )
        errors.append(error)

    if errors:
        return errors

    decimal_places = abs(geoX['value'].as_tuple().exponent)
    if decimal_places > MAX_DECIMAL_PLACES:
        message = f"{geoX['value']} should not have more than six decimal places"
        error = Error(
            'geo-error',
            cell=geoX,
            row_number=cell['row-number'],
            message=message
        )
        errors.append(error)

    if errors:
        return errors

    if geoX['value'] < -7 or geoX['value'] > 2:
        message = f"{geoX['value']} is not a longitude within the UK"
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

    if abs(geoY['value']) > 90:
        message = f"{geoY['value']} isn't a latitude using the WGS84 or ETRS89 coordinate systems"
        error = Error(
            'geo-error',
            cell=geoY,
            row_number=cell['row-number'],
            message=message
        )
        errors.append(error)

    if errors:
        return errors

    decimal_places = abs(geoY['value'].as_tuple().exponent)
    if decimal_places > 6:
        message = f"{geoY['value']} should not have more than six decimal places"
        error = Error(
            'geo-error',
            cell=geoY,
            row_number=cell['row-number'],
            message=message
        )
        errors.append(error)

    if errors:
        return errors

    if geoY['value'] < 49 or geoY['value'] > 57:
        message = f"{geoY['value']} is not a latitude within the UK"
        error = Error(
            'geo-error',
            cell=geoY,
            row_number=cell['row-number'],
            message=message
        )
        errors.append(error)

    return errors

