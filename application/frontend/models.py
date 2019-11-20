import uuid

from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from application.extensions import db


class ValidationReport(db.Model):

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_result = db.Column(JSONB, default=dict)
    original_data = db.Column(JSONB, default=dict)
    validated_data = db.Column(JSONB, default=dict)
    errors_by_column = db.Column(JSONB, default=dict)
    errors_by_row = db.Column(JSONB, default=dict)
    additional_data = db.Column(JSONB, default=dict)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

    def __init__(self, report):
        original_data = report.original_data
        validated_data = report.validated_data
        raw_result = report.raw_result
        additional_data = report.additional_data
        errors_by_column = report.errors_by_column
        errors_by_row = report.errors_by_row
        super(ValidationReport, self).__init__(raw_result=raw_result,
                                               original_data=original_data,
                                               validated_data=validated_data,
                                               additional_data=additional_data,
                                               errors_by_column=errors_by_column,
                                               errors_by_row=errors_by_row)

    def to_dict(self):
        return {
            'id': str(self.id),
            'raw_result': self.raw_result,
            'original_data': self.original_data,
            'validated_data': self.validated_data,
            'additional_data': self.additional_data,
            'errors_by_row': self.errors_by_row,
            'errors_by_column': self.errors_by_column
        }
