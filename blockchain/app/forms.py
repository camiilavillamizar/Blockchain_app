from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import InputRequired, Email

class InscriptionForm(FlaskForm):
    name = StringField('Name', [InputRequired("Please enter your name")], render_kw={"placeholder": "Name"})
    user_name = StringField('Username', [InputRequired("Please enter an username.")], render_kw={"placeholder":"Username"})
    email = StringField('Email', [InputRequired("Please enter your email address."), Email("This field requires a valid email address.")], render_kw={"placeholder":"Email"})
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    user_name = StringField('Username', [InputRequired("Please enter your username.")])

class UpdateNameForm(FlaskForm):
    name = StringField('Name', [InputRequired("Please enter your name.")])

class TransactionForm(FlaskForm):
    content = TextAreaField('Content', [InputRequired("Please write somethingg.")])
