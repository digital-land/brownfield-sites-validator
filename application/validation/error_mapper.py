from datetime import datetime

import dateparser


class ErrorMapper:

    error_messages = {
        "schema-error": "Schema is not valid",
        "non-matching-header": "The header's name in the schema is different from what's in the data",
        "extra-header": "The data contains a header not defined in the schema",
        "missing-header": "The data doesn't contain a header defined in the schema",
        "type-or-format-error": "The data doesn't match expected format.",
        "required-constraint": "This field is a required field, but it contains no value",
        "pattern-constraint": "This field value's should conform to the defined pattern",
        "unique-constraint": "This field is a unique field but it contains a value that has been used in another row",
        "enumerable-constraint": "This field value should be equal to one of the values in the enumeration constraint",
        "minimum-constraint": "This field value should be greater or equal than constraint value",
        "maximum-constraint": "This field value should be less or equal than constraint value",
        "minimum-length-constraint": "A length of this field value should be greater or equal than schema constraint value",
        "maximum-length-constraint": "A length of this field value should be less or equal than schema constraint value"
    }

    def __init__(self, raw_error):
        self.raw_error = raw_error

    def overall_error_message(self):
        if self.raw_error['code'] == 'type-or-format-error':
            if self.raw_error['message-data']['field_type'] == 'date':
                today = datetime.today()
                today_human = today.strftime('%d/%m/%Y')
                today_iso = today.strftime('%Y-%m-%d')
                return f'Some dates in the file are not in the format YYYY-MM-DD. For example {today_human} should be {today_iso}'
        if self.raw_error['code'] == 'pattern-constraint':
            return f"Some entries in this columns don't match the value '{self.raw_error['message-data']['constraint']}'"

    def field_error_message(self):
        message = 'Cannot map error message'
        if self.raw_error['code'] == 'type-or-format-error':
            if self.raw_error['message-data']['field_type'] == 'date':
                date_provided = self.raw_error['message-data']['value']
                d = dateparser.parse(date_provided)
                valid_date = d.strftime('%Y-%m-%d')
                message = f'The date {date_provided} should be entered as {valid_date}'
        if self.raw_error['code'] == 'pattern-constraint':
            message = f"The field contained '{self.raw_error['message-data']['value']}' but should have been '{self.raw_error['message-data']['constraint']}'"

        return message