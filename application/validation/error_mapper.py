import dateparser

from abc import ABC, abstractmethod
from datetime import datetime

from application.validation.utils import get_markdown_for_field


class ErrorMapper(ABC):

    @staticmethod
    def factory(error, field):
        if error['code'] == 'type-or-format-error':
            return TypeOrFormatErrorMapper(error, field)
        if error['code'] == 'pattern-constraint':
            return PatternErrorMapper(error, field)
        if error['code'] == 'non-matching-header':
            return HeaderErrorMapper(error, field)
        if error['code'] == 'geo-error':
            return GeoErrorMapper(error, field)
        if error['code'] == 'required-constraint':
            return RequiredErrorMapper(error, field)
        return UnknownErrorMapper(error, field)

    def __init__(self, raw_error, field):
        self.raw_error = raw_error
        self.field = field

    @abstractmethod
    def overall_error_messages(self) -> None:
        pass

    @abstractmethod
    def field_error_message(self) -> None:
        pass


class TypeOrFormatErrorMapper(ErrorMapper):

    def overall_error_messages(self):
        if self.raw_error['message-data']['field_type'] == 'date':
            today = datetime.today()
            today_human = today.strftime('%d/%m/%Y')
            today_iso = today.strftime('%Y-%m-%d')
            message = f'Some dates in the file are not in the format YYYY-MM-DD. For example {today_human} should be {today_iso}'
        elif self.raw_error['message-data']['field_type'] == 'number':
            message = "Some entries in this column are non numeric"
        return message

    def field_error_message(self):
        if self.raw_error['message-data']['field_type'] == 'date':
            date_provided = self.raw_error['message-data']['value']
            d = dateparser.parse(date_provided)
            valid_date = d.strftime('%Y-%m-%d')
            message = f'The date {date_provided} should be entered as {valid_date}'
        elif self.raw_error['message-data']['field_type'] == 'number':
            message = f"{self.raw_error['message-data']['value']} is not a valid number"
        return message


class PatternErrorMapper(ErrorMapper):

    def overall_error_messages(self):
        try:
            return get_markdown_for_field(self.field)
        except Exception as e:
            return 'Unknown'

    def field_error_message(self):
        return f"The entry was '{self.raw_error['message-data']['value']}'"


class GeoErrorMapper(ErrorMapper):

    def overall_error_messages(self):
        return "GeoX or GeoY should represent a point in UK using the WGS84 or ETRS89 coordinate systems."

    def field_error_message(self):
        return self.raw_error['message']


class HeaderErrorMapper(ErrorMapper):

    def overall_error_messages(self):
        return f"The header should have been {self.raw_error['message-data']['field_name']}"

    def field_error_message(self):
        return f"The header {self.raw_error['message-data']['header']} should have been {self.raw_error['message-data']['field_name']}"


class RequiredErrorMapper(ErrorMapper):

    def overall_error_messages(self):
        return "Some entries in this column are empty"

    def field_error_message(self):
        return f"{self.field} can't be empty"


class UnknownErrorMapper(ErrorMapper):

    def overall_error_messages(self):
        return 'Unknown error message'

    def field_error_message(self):
        return f'There was an unknown error with {self.field}'