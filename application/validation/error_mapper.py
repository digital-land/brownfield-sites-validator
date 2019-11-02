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
        message = 'Unknown error message'
        if self.raw_error['code'] == 'type-or-format-error':
            if self.raw_error['message-data']['field_type'] == 'date':
                today = datetime.today()
                today_human = today.strftime('%d/%m/%Y')
                today_iso = today.strftime('%Y-%m-%d')
                message = f'Some dates in the file are not in the format YYYY-MM-DD. For example {today_human} should be {today_iso}'
            elif self.raw_error['message-data']['field_type'] == 'number':
                message = "This column should only have numeric data and some entries are non numeric"

        elif self.raw_error['code'] == 'pattern-constraint':
            cleaned_up = self._clean_up(self.raw_error['message-data']['constraint'])
            message = f"Some entries in this columns don't match the value '{cleaned_up}'"
        elif self.raw_error['code'] == 'non-matching-header':
            message = f"The header should have been {self.raw_error['message-data']['field_name']}"
        elif self.raw_error['code'] == 'geo-error':
            message = f"There was a {self.raw_error['code']}"
        return message

    def field_error_message(self):
        message = 'Unknown error message'
        if self.raw_error['code'] == 'type-or-format-error':
            if self.raw_error['message-data']['field_type'] == 'date':
                date_provided = self.raw_error['message-data']['value']
                d = dateparser.parse(date_provided)
                valid_date = d.strftime('%Y-%m-%d')
                message = f'The date {date_provided} should be entered as {valid_date}'
            elif self.raw_error['message-data']['field_type'] == 'number':
                message = f"{self.raw_error['message-data']['value']} is not a valid number"
        elif self.raw_error['code'] == 'pattern-constraint':
            cleaned_up = self._clean_up(self.raw_error['message-data']['constraint'])
            message = f"The field contained '{self.raw_error['message-data']['value']}' but should have been '{cleaned_up}'"
        elif self.raw_error['code'] == 'non-matching-header':
            message = f"The header {self.raw_error['message-data']['header']} should have been {self.raw_error['message-data']['field_name']}"
        elif self.raw_error['code'] == 'geo-error':
            message = self.raw_error['message']

        return message

    def _clean_up(self, pattern):
        return ' or '.join(self.raw_error['message-data']['constraint']\
            .replace('(?i)', '')\
            .replace('(', '')\
            .replace(')', '')\
            .split('|'))