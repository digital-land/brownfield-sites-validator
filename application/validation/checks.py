from goodtables import Error, check


@check('geox-check', type='custom', context='body')
def geox_check(cells):
    errors = []
    for cell in cells:
        if cell.get('header') is not None and cell.get('header') == 'GeoX':
            geoX = cell
            break
    try:
        geoX_value = float(geoX['value'])
    except Exception as e:
        message = f"GeoX {geoX['value']} is not a decimal number"
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
        message = f"GeoX (longitude) {geoX_value} may be out of bounds for the UK"
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
    for cell in cells:
        if cell.get('header') is not None and cell.get('header') == 'GeoY':
            geoY = cell
            break
    try:
        geoY_value = float(geoY['value'])
    except Exception as e:
        message = f"GeoY {geoY['value']} is not a decimal number"
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
        message = f"GeoY (latitude) {geoY_value} may be out of bounds for the UK"
        error = Error(
            'geo-error',
            cell=geoY,
            row_number=cell['row-number'],
            message=message
        )
        errors.append(error)

    return errors

