from flask_wtf          import FlaskForm
from wtforms            import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from cus_app.models         import User
#
#--- FlaskForm gives a pre-made "submission" form 
#
class LoginForm(FlaskForm):
    username    = StringField('Username',   validators=[DataRequired()])
    password    = PasswordField('Password', validators=[DataRequired()])
    submit      = SubmitField('Sign In')

