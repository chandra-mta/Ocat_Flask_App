from flask_wtf          import FlaskForm
from wtforms            import StringField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Length


class SubmitForm(FlaskForm):
    obsidrev    = StringField('ObsidRev', validators=[DataRequired()])
    submit      = SubmitField('Submit')
