from flask_wtf import FlaskForm
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired


class BrownfieldSiteURLForm(FlaskForm):

    url = URLField('URL', validators=[DataRequired()])
