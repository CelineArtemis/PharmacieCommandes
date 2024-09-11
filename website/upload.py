from flask_wtf import FlaskForm
from wtforms import FileField
from wtforms.validators import DataRequired


class UploadForm(FlaskForm):
    file = FileField('file', validators=[DataRequired()])