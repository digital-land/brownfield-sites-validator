from flask_wtf import FlaskForm
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired, ValidationError


class BrownfieldSiteURLForm(FlaskForm):

    url = URLField('URL', validators=[DataRequired()])

    # TODO this will probably go as we may just try and covert to csv if xls/xlsx etc?
    def validate_url(form, field):
        if not field.data.endswith('.csv'):
            raise ValidationError('Brownfield register must be a csv file')
