from flask              import request
from flask_wtf          import FlaskForm
from wtforms            import StringField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Length
from app.models         import User


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')
