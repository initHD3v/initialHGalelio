from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    TextAreaField,
    FileField,
    SelectField,
    DateField,
    DateTimeField,
    BooleanField,
    HiddenField,
    FloatField,  # Moved FloatField to top
)
from wtforms.validators import (
    DataRequired,
    EqualTo,
    ValidationError,
    Email,
    NumberRange,
    Optional,
)
from wtforms_sqlalchemy.fields import QuerySelectField
from models import User, WeddingPackage, BankAccount # Added BankAccount
from extensions import db # Added import
from datetime import datetime # Added datetime import

def get_active_bank_accounts():
    accounts = BankAccount.query.filter_by(is_active=True).order_by(BankAccount.bank_name)
    print(f"DEBUG: Active bank accounts query: {accounts.all()}") # Added debug print
    return accounts


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    full_name = StringField("Nama Lengkap", validators=[DataRequired()])
    username = StringField("Nama Panggilan (untuk login)", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    whatsapp_number = StringField("Nomor WhatsApp", validators=[DataRequired()])

    def validate_whatsapp_number(self, whatsapp_number):
        # Remove any non-digit characters except '+'
        cleaned_number = "".join(
            filter(lambda x: x.isdigit() or x == "+", whatsapp_number.data)
        )

        if cleaned_number.startswith("0"):
            cleaned_number = "+62" + cleaned_number[1:]
        elif not cleaned_number.startswith("+62"):
            cleaned_number = "+62" + cleaned_number

        # Update the field data with the normalized number
        whatsapp_number.data = cleaned_number

        # Basic length validation after normalization
        if len(whatsapp_number.data) < 10 or len(whatsapp_number.data) > 15:
            raise ValidationError("Nomor WhatsApp tidak valid.")

    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "That username is taken. Please choose a different one."
            )

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("That email is taken. Please choose a different one.")


class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    content = TextAreaField("Content", validators=[DataRequired()])
    image = FileField("Images")  # Akan diatur multiple di template
    submit = SubmitField("Post")


class OrderForm(FlaskForm):
    service_type = SelectField(
        "Service Type",
        choices=[
            ("wedding", "Wedding"),
            ("prewedding", "Pre-Wedding"),
            ("event", "Event"),
            ("portrait", "Portrait"),
        ],
        validators=[DataRequired()],
    )
    wedding_package = QuerySelectField(
        "Wedding Package",
        query_factory=lambda: WeddingPackage.query.filter_by(category='Wedding').all(),
        get_label=lambda x: x.name,
        get_pk=lambda x: x.id,
        allow_blank=True,
        blank_text="-- Select a Wedding package --",
        validators=[Optional()] # Make optional, will be required conditionally
    )
    prewedding_package = QuerySelectField(
        "Pre-wedding Package",
        query_factory=lambda: WeddingPackage.query.filter_by(category='Pre-wedding').all(),
        get_label=lambda x: x.name,
        get_pk=lambda x: x.id,
        allow_blank=True,
        blank_text="-- Select a Pre-wedding package --",
        validators=[Optional()] # Make optional, will be required conditionally
    )
    event_date = DateField("Event Date", format="%Y-%m-%d", validators=[DataRequired()])
    event_start_time = StringField("Start Time", validators=[Optional()])
    event_end_time = StringField("End Time", validators=[Optional()])
    location = StringField("Location", validators=[DataRequired()])
    latitude = HiddenField()
    longitude = HiddenField()
    details = TextAreaField("Details")
    total_price = FloatField("Total Price", validators=[Optional()]) # Still optional, will be calculated
    submit = SubmitField("Place Order")


class TestimonialForm(FlaskForm):
    client_name = StringField("Client Name", validators=[DataRequired()])
    testimonial_text = TextAreaField("Testimonial", validators=[DataRequired()])
    rating = SelectField(
        "Rating",
        choices=[
            (1, "1 Star"),
            (2, "2 Stars"),
            (3, "3 Stars"),
            (4, "4 Stars"),
            (5, "5 Stars"),
        ],
        coerce=int,
        validators=[DataRequired()],
    )
    is_approved = BooleanField("Approve Testimonial")
    submit = SubmitField("Save Testimonial")


class TestimonialSubmissionForm(FlaskForm):
    testimonial_text = TextAreaField("Your Testimonial", validators=[DataRequired()])
    rating = SelectField(
        "Rating",
        choices=[
            (1, "1 Star"),
            (2, "2 Stars"),
            (3, "3 Stars"),
            (4, "4 Stars"),
            (5, "5 Stars"),
        ],
        coerce=int,
        validators=[DataRequired()],
    )
    submit = SubmitField("Submit Testimonial")


class TestimonialEditForm(FlaskForm):
    testimonial_text = TextAreaField("Your Testimonial", validators=[DataRequired()])
    rating = SelectField(
        "Rating",
        choices=[
            (1, "1 Star"),
            (2, "2 Stars"),
            (3, "3 Stars"),
            (4, "4 Stars"),
            (5, "5 Stars"),
        ],
        coerce=int,
        validators=[DataRequired()],
    )
    submit = SubmitField("Update Testimonial")


class UserEditForm(FlaskForm):
    full_name = StringField("Nama Lengkap", validators=[DataRequired()])
    username = StringField("Nama Panggilan (untuk login)", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    whatsapp_number = StringField("Nomor WhatsApp", validators=[DataRequired()])
    company_name = StringField("Nama Perusahaan (Admin Saja)", validators=[Optional()])
    company_address = TextAreaField("Alamat Perusahaan (Admin Saja)", validators=[Optional()])
    company_email = StringField("Email Perusahaan (Admin Saja)", validators=[Optional(), Email()])
    company_phone = StringField("Telepon Perusahaan (Admin Saja)", validators=[Optional()])
    password = PasswordField("New Password (leave blank to keep current)")
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[EqualTo("password", message="Passwords must match")],
    )
    submit = SubmitField("Update Profile")

    def __init__(self, original_username, original_email, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(
                    "That username is taken. Please choose a different one."
                )

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(
                    "That email is taken. Please choose a different one."
                )


class DPPaymentForm(FlaskForm):
    bank_account = QuerySelectField(
        "Pilih Rekening Bank Tujuan",
        query_factory=get_active_bank_accounts,
        get_label=lambda x: f"{x.bank_name} - {x.account_name} ({x.account_number})",
        allow_blank=False,
        validators=[DataRequired()]
    )
    payment_proof = FileField("Upload Bukti Pembayaran", validators=[DataRequired()])
    submit = SubmitField("Kirim Bukti Pembayaran")


class CalendarEventForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    start_time = DateTimeField(
        "Start Time", format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    end_time = DateTimeField(
        "End Time", format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    description = TextAreaField("Description")
    is_available = BooleanField("Is Available")
    submit = SubmitField("Save Event")


class WeddingPackageForm(FlaskForm):
    name = StringField("Package Name", validators=[DataRequired()])
    description = TextAreaField("Description")
    price = FloatField(
        "Price",
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="Price must be greater than zero."),
        ],
    )
    category = SelectField(
        "Category",
        choices=[('Wedding', 'Wedding'), ('Pre-wedding', 'Pre-wedding'), ('Event', 'Event')],
        validators=[DataRequired()]
    )
    submit = SubmitField("Save Package")


class BankAccountForm(FlaskForm):
    bank_name = StringField("Nama Bank", validators=[DataRequired()])
    account_number = StringField("Nomor Rekening", validators=[DataRequired()])
    account_name = StringField("Nama Pemilik Rekening", validators=[DataRequired()])
    is_active = BooleanField("Aktifkan Rekening Ini")
    submit = SubmitField("Simpan Rekening")

    def validate_account_number(self, account_number):
        if not account_number.data.isdigit():
            raise ValidationError("Nomor Rekening harus berupa angka.")


class AdminOrderForm(FlaskForm):
    service_type = SelectField(
        "Service Type",
        choices=[
            ("wedding", "Wedding"),
            ("prewedding", "Pre-Wedding"),
            ("event", "Event"),
            ("portrait", "Portrait"),
        ],
        validators=[DataRequired()],
    )
    wedding_package = QuerySelectField(
        "Wedding Package",
        query_factory=lambda: WeddingPackage.query.filter_by(category='Wedding').all(),
        get_label=lambda x: x.name,
        get_pk=lambda x: x.id,
        allow_blank=True,
        blank_text="-- Select a Wedding package --",
        validators=[Optional()]
    )
    prewedding_package = QuerySelectField(
        "Pre-wedding Package",
        query_factory=lambda: WeddingPackage.query.filter_by(category='Pre-wedding').all(),
        get_label=lambda x: x.name,
        get_pk=lambda x: x.id,
        allow_blank=True,
        blank_text="-- Select a Pre-wedding package --",
        validators=[Optional()]
    )
    event_date = DateField("Event Date", format="%Y-%m-%d", validators=[DataRequired()])
    event_start_time = StringField("Start Time", validators=[Optional()])
    event_end_time = StringField("End Time", validators=[Optional()])
    location = StringField("Location", validators=[DataRequired()])
    latitude = HiddenField()
    longitude = HiddenField()
    details = TextAreaField("Details")
    total_price = FloatField("Total Price", validators=[DataRequired(), NumberRange(min=0.01, message="Price must be greater than zero.")])
    
    # Admin-specific fields
    status = SelectField(
        "Status",
        choices=[
            ("waiting_dp", "Waiting DP"),
            ("waiting_approval", "Waiting Approval"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
            ("completed", "Completed"),
        ],
        validators=[DataRequired()],
    )
    bank_account = QuerySelectField(
        "Bank Account for Payment",
        query_factory=get_active_bank_accounts,
        get_label=lambda x: f"{x.bank_name} - {x.account_name} ({x.account_number})",
        allow_blank=True,
        blank_text="-- Select a Bank Account --",
        validators=[Optional()]
    )
    
    submit = SubmitField("Save Changes")

    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False

        # Conditional validation for event_start_time and event_end_time
        if self.service_type.data != "prewedding":
            if not self.event_start_time.data:
                self.event_start_time.errors.append("Start Time is required for this service type.")
                initial_validation = False
            if not self.event_end_time.data:
                self.event_end_time.errors.append("End Time is required for this service type.")
                initial_validation = False
            
            if self.event_start_time.data and self.event_end_time.data:
                try:
                    start_time_obj = datetime.strptime(self.event_start_time.data, "%H:%M").time()
                    end_time_obj = datetime.strptime(self.event_end_time.data, "%H:%M").time()
                    if start_time_obj >= end_time_obj:
                        self.event_end_time.errors.append("End Time must be after Start Time.")
                        initial_validation = False
                except ValueError:
                    self.event_start_time.errors.append("Invalid time format. Please use HH:MM.")
                    self.event_end_time.errors.append("Invalid time format. Please use HH:MM.")
                    initial_validation = False
        
        # Conditional validation for packages
        if self.service_type.data == "wedding" and not self.wedding_package.data:
            self.wedding_package.errors.append("Wedding Package is required for Wedding service.")
            initial_validation = False
        elif self.service_type.data == "prewedding" and not self.prewedding_package.data:
            self.prewedding_package.errors.append("Pre-wedding Package is required for Pre-wedding service.")
            initial_validation = False

        return initial_validation


class HomepageContentForm(FlaskForm):
    about_text = TextAreaField("Teks Tentang Aruna Moment", validators=[DataRequired()])
    about_image = FileField("Gambar Profil/Studio (Opsional)")
    hero_images = FileField("Unggah Gambar Hero Baru (Bisa Lebih Dari Satu)", render_kw={'multiple': True})
    submit = SubmitField("Simpan Perubahan Homepage")