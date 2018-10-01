from application.validators.validators import ValidationError, ValidationWarning


def format_error(error):
    return ValidationError[error].value


def format_warning(warning):
    return ValidationWarning[warning].value


def healthcheck(validation_dict):
    # @colm this is just a silly idea about how to indicate health of data in index page, maybe a score instead?
    # so please change for something better
    if not validation_dict.get('errors') and not validation_dict.get('warnings') and not validation_dict.get('file_warnings') and not validation_dict.get('file_errors'):
        return 'Good'
    if not validation_dict.get('errors') and validation_dict.get('file_warnings') or validation_dict.get('file_errors') or validation_dict.get('warnings'):
        return 'Needs minor improvement'
    if validation_dict.get('errors'):
        return 'Needs major improvement'


def format_date_time(date_time):
    return date_time.strftime('%d %b %Y %-H:%M')