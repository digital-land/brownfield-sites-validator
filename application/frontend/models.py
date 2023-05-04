import uuid

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm.attributes import flag_modified
from application.extensions import db


class ResultModel(db.Model):

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result = db.Column(JSONB, default=dict)
    input = db.Column(JSONB, default=dict)
    rows = db.Column(JSONB, default=dict)
    errors_by_column = db.Column(JSONB, default=dict)
    errors_by_row = db.Column(JSONB, default=list)
    meta_data = db.Column(JSONB, default=dict)
    created_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(), nullable=True, onupdate=func.now())

    def __init__(self, validation_result):
        input = validation_result.input
        rows = validation_result.rows
        result = validation_result.result
        meta_data = validation_result.meta_data
        errors_by_column = validation_result.errors_by_column
        errors_by_row = validation_result.errors_by_row
        super(ResultModel, self).__init__(
            result=result,
            input=input,
            rows=rows,
            meta_data=meta_data,
            errors_by_column=errors_by_column,
            errors_by_row=errors_by_row,
        )

    def to_dict(self):
        return {
            "id": str(self.id),
            "result": self.result,
            "input": self.input,
            "rows": self.rows,
            "meta_data": self.meta_data,
            "errors_by_row": self.errors_by_row,
            "errors_by_column": self.errors_by_column,
        }

    def update(self, validation_result):
        self.result = validation_result.result
        self.rows = validation_result.rows
        self.meta_data = validation_result.meta_data
        self.errors_by_column = validation_result.errors_by_column
        self.errors_by_row = validation_result.errors_by_row

        flag_modified(self, "result")
        flag_modified(self, "rows")
        flag_modified(self, "meta_data")
        flag_modified(self, "errors_by_column")
        flag_modified(self, "errors_by_row")
