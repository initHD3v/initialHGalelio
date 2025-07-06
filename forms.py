from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField, SelectField, DateField, DateTimeField, BooleanField, HiddenField, FloatField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Email, NumberRange, Optional
from wtforms_sqlalchemy.fields import QuerySelectField
from models import User, WeddingPackage


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    full_name = StringField('Nama Lengkap', validators=[DataRequired()])
    username = StringField('Nama Panggilan (untuk login)', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    whatsapp_number = StringField('Nomor WhatsApp', validators=[DataRequired()])

    def validate_whatsapp_number(self, whatsapp_number):
        # Remove any non-digit characters except '+'
        cleaned_number = ''.join(filter(lambda x: x.isdigit() or x == '+', whatsapp_number.data))

        if cleaned_number.startswith('0'):
            cleaned_number = '+62' + cleaned_number[1:]
        elif not cleaned_number.startswith('+62'):
            cleaned_number = '+62' + cleaned_number
        
        # Update the field data with the normalized number
        whatsapp_number.data = cleaned_number

        # Basic length validation after normalization
        if len(whatsapp_number.data) < 10 or len(whatsapp_number.data) > 15:
            raise ValidationError('Nomor WhatsApp tidak valid.')
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    image = FileField('Images') # Akan diatur multiple di template
    submit = SubmitField('Post')

class OrderForm(FlaskForm):
    service_type = SelectField('Service Type', choices=[('wedding', 'Wedding'), ('prewedding', 'Pre-Wedding'), ('event', 'Event'), ('portrait', 'Portrait')], validators=[DataRequired()])
    wedding_package = QuerySelectField('Wedding Package', query_factory=lambda: WeddingPackage.query.all(), get_label=lambda x: x.name, get_pk=lambda x: x.id, allow_blank=True, blank_text='-- Select a package --')
    event_date = DateField('Event Date', format='%Y-%m-%d', validators=[DataRequired()])
    event_start_time = StringField('Start Time', validators=[DataRequired()])
    event_end_time = StringField('End Time', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    latitude = HiddenField()
    longitude = HiddenField()
    details = TextAreaField('Details')
    total_price = FloatField('Total Price', validators=[Optional()])
    submit = SubmitField('Place Order')

class TestimonialForm(FlaskForm):
    client_name = StringField('Client Name', validators=[DataRequired()])
    testimonial_text = TextAreaField('Testimonial', validators=[DataRequired()])
    rating = SelectField('Rating', choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], coerce=int, validators=[DataRequired()])
    is_approved = BooleanField('Approve Testimonial')
    submit = SubmitField('Save Testimonial')

class TestimonialSubmissionForm(FlaskForm):
    testimonial_text = TextAreaField('Your Testimonial', validators=[DataRequired()])
    rating = SelectField('Rating', choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit Testimonial')

class TestimonialEditForm(FlaskForm):
    testimonial_text = TextAreaField('Your Testimonial', validators=[DataRequired()])
    rating = SelectField('Rating', choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], coerce=int, validators=[DataRequired()])
    submit = SubmitField('Update Testimonial')

class UserEditForm(FlaskForm):
    full_name = StringField('Nama Lengkap', validators=[DataRequired()])
    username = StringField('Nama Panggilan (untuk login)', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    whatsapp_number = StringField('Nomor WhatsApp', validators=[DataRequired()])
    password = PasswordField('New Password (leave blank to keep current)')
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Update Profile')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')

from wtforms import FloatField

class DPPaymentForm(FlaskForm):
    payment_proof = FileField('Upload Bukti Pembayaran', validators=[DataRequired()])
    submit = SubmitField('Kirim Bukti Pembayaran')

class CalendarEventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    start_time = DateTimeField('Start Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_time = DateTimeField('End Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    description = TextAreaField('Description')
    is_available = BooleanField('Is Available')
    submit = SubmitField('Save Event')

class WeddingPackageForm(FlaskForm):
    name = StringField('Package Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0.01, message='Price must be greater than zero.')])
    submit = SubmitField('Save Package')
