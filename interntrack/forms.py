"""Server-side validation shared by create and edit workflows."""
from datetime import date
from urllib.parse import urlsplit
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, DateTimeLocalField, SubmitField
from wtforms.validators import InputRequired, Length, EqualTo, Optional, Regexp, ValidationError
from .models import STATUSES


def strip(value):
    return value.strip() if isinstance(value, str) else value


def http_url(form, field):
    value = field.data
    try:
        parsed = urlsplit(value)
        port = parsed.port
        valid = parsed.scheme.lower() in ('http', 'https') and parsed.hostname and not parsed.username and not parsed.password
        if not valid or any(c.isspace() or ord(c) < 32 for c in value) or '\\' in value:
            raise ValueError()
    except ValueError:
        raise ValidationError('Enter a complete http:// or https:// URL without spaces or credentials.')


class RegisterForm(FlaskForm):
    username = StringField('Username', filters=[strip, lambda v: v.lower() if v else v], validators=[InputRequired(), Length(min=3, max=40), Regexp(r'^[a-z0-9_.-]+$', message='Use letters, numbers, dots, hyphens, or underscores.')])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=10, max=128)])
    confirm = PasswordField('Confirm password', validators=[InputRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Create account')


class LoginForm(FlaskForm):
    username = StringField('Username', filters=[strip, lambda v: v.lower() if v else v], validators=[InputRequired(), Length(max=40)])
    password = PasswordField('Password', validators=[InputRequired(), Length(max=128)])
    submit = SubmitField('Sign in')


class ApplicationForm(FlaskForm):
    company = StringField('Company', filters=[strip], validators=[InputRequired(), Length(min=1, max=100)])
    position = StringField('Position', filters=[strip], validators=[InputRequired(), Length(min=1, max=150)])
    applied_date = DateField('Application date', validators=[InputRequired()], default=date.today)
    status = SelectField('Status', choices=[(s, s) for s in STATUSES], validators=[InputRequired()])
    job_url = StringField('Job posting URL (optional)', filters=[strip], validators=[Optional(), Length(max=1000), http_url])
    interview_datetime = DateTimeLocalField('Interview date and time (optional)', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    notes = TextAreaField('Notes (optional)', filters=[strip], validators=[Optional(), Length(max=5000)])
    submit = SubmitField('Save application')


class ActionForm(FlaskForm):
    submit = SubmitField('Confirm')
