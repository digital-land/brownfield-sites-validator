from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired


class UploadForm(FlaskForm):

    upload = FileField('file', validators=[
        FileRequired()
    ])