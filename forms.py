from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, TimeField, FloatField, BooleanField, IntegerField, SubmitField, HiddenField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
from models import User
from datetime import date

# User Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('officer', 'Police Officer'), ('analyst', 'Analyst'), ('admin', 'Administrator')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    submit = SubmitField('Update Profile')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already registered. Please use a different one.')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

# Crime Forms
class CrimeForm(FlaskForm):
    type = StringField('Crime Type', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], default=date.today)
    time = TimeField('Time', validators=[Optional()])
    location = StringField('Location', validators=[DataRequired(), Length(max=255)])
    latitude = FloatField('Latitude', validators=[Optional()])
    longitude = FloatField('Longitude', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('reported', 'Reported'),
        ('investigating', 'Under Investigation'),
        ('solved', 'Solved'),
        ('closed', 'Closed')
    ])
    submit = SubmitField('Submit')

class CrimeSearchForm(FlaskForm):
    search_term = StringField('Search')
    crime_type = StringField('Crime Type')
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    location = StringField('Location')
    status = SelectField('Status', choices=[
        ('', 'All'),
        ('reported', 'Reported'),
        ('investigating', 'Under Investigation'),
        ('solved', 'Solved'),
        ('closed', 'Closed')
    ], validators=[Optional()])
    submit = SubmitField('Search')

# Criminal Forms
class CriminalForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    alias = StringField('Alias/Nickname', validators=[Optional(), Length(max=100)])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    address = StringField('Address', validators=[Optional(), Length(max=255)])
    nationality = StringField('Nationality', validators=[Optional(), Length(max=50)])
    identification_marks = StringField('Identification Marks', validators=[Optional(), Length(max=255)])
    photo_url = StringField('Photo URL', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Submit')

class CriminalSearchForm(FlaskForm):
    search_term = StringField('Search')
    gender = SelectField('Gender', choices=[
        ('', 'All'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], validators=[Optional()])
    nationality = StringField('Nationality')
    submit = SubmitField('Search')

# Case Forms
class CaseForm(FlaskForm):
    title = StringField('Case Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('closed', 'Closed')
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ])
    crime_id = SelectField('Related Crime', coerce=int, validators=[DataRequired()])
    officer_id = SelectField('Assign Officer', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

class CaseNoteForm(FlaskForm):
    content = TextAreaField('Note', validators=[DataRequired()])
    submit = SubmitField('Add Note')

class CaseSearchForm(FlaskForm):
    search_term = StringField('Search')
    status = SelectField('Status', choices=[
        ('', 'All'),
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('closed', 'Closed')
    ], validators=[Optional()])
    priority = SelectField('Priority', choices=[
        ('', 'All'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], validators=[Optional()])
    officer_id = SelectField('Officer', coerce=int, validators=[Optional()])
    submit = SubmitField('Search')

# Victim Forms
class VictimForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    age = IntegerField('Age', validators=[Optional()])
    contact = StringField('Contact', validators=[Optional(), Length(max=50)])
    address = StringField('Address', validators=[Optional(), Length(max=255)])
    statement = TextAreaField('Statement', validators=[Optional()])
    crime_id = SelectField('Related Crime', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

# Witness Forms
class WitnessForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    contact = StringField('Contact', validators=[Optional(), Length(max=50)])
    address = StringField('Address', validators=[Optional(), Length(max=255)])
    statement = TextAreaField('Statement', validators=[Optional()])
    relation_to_victim = StringField('Relation to Victim', validators=[Optional(), Length(max=100)])
    crime_id = SelectField('Related Crime', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

# Evidence Forms
class EvidenceForm(FlaskForm):
    name = StringField('Evidence Name', validators=[DataRequired(), Length(max=100)])
    type = StringField('Type', validators=[Optional(), Length(max=50)])
    description = TextAreaField('Description', validators=[Optional()])
    location_found = StringField('Location Found', validators=[Optional(), Length(max=255)])
    collection_date = DateField('Collection Date', validators=[Optional()])
    custodian = StringField('Custodian', validators=[Optional(), Length(max=100)])
    storage_location = StringField('Storage Location', validators=[Optional(), Length(max=255)])
    crime_id = SelectField('Related Crime', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

# Police Station Forms
class PoliceStationForm(FlaskForm):
    name = StringField('Station Name', validators=[DataRequired(), Length(max=100)])
    address = StringField('Address', validators=[DataRequired(), Length(max=255)])
    contact = StringField('Contact', validators=[Optional(), Length(max=50)])
    latitude = FloatField('Latitude', validators=[Optional()])
    longitude = FloatField('Longitude', validators=[Optional()])
    submit = SubmitField('Submit')

# Police Officer Forms
class PoliceOfficerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    rank = StringField('Rank', validators=[DataRequired(), Length(max=50)])
    badge_number = StringField('Badge Number', validators=[DataRequired(), Length(max=50)])
    contact = StringField('Contact', validators=[Optional(), Length(max=50)])
    user_id = SelectField('User Account', coerce=int, validators=[Optional()])
    station_id = SelectField('Police Station', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')
