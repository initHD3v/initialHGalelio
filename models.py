from flask_login import UserMixin
from datetime import datetime, UTC
from extensions import db
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)  # Nickname
    email = db.Column(db.String(150), unique=True, nullable=False)
    whatsapp_number = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(
        db.String(50), default="client", nullable=False
    )  # 'admin' or 'client'
    company_name = db.Column(db.String(200), nullable=True)
    company_address = db.Column(db.String(200), nullable=True)
    company_email = db.Column(db.String(150), nullable=True)
    company_phone = db.Column(db.String(20), nullable=True)
    date_registered = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    orders = db.relationship("Order", backref="client", lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except Exception:
            return None
        return User.query.get(user_id)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_hidden = db.Column(
        db.Boolean, default=False, nullable=False
    )  # New field for visibility
    images = db.relationship(
        "PostImage", backref="post", lazy=True, cascade="all, delete-orphan"
    )


class PostImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    filename = db.Column(db.String(150), nullable=False)
    likes = db.Column(db.Integer, default=0, nullable=False)
    image_likes = db.relationship("ImageLike", backref="post_image", lazy=True, cascade="all, delete-orphan")


class ImageLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_image_id = db.Column(
        db.Integer, db.ForeignKey("post_image.id"), nullable=False
    )
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Ensure a user can only like a specific image once
    __table_args__ = (
        db.UniqueConstraint("user_id", "post_image_id", name="_user_image_uc"),
    )

    user = db.relationship("User", backref="image_likes")


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    service_type = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    event_start_time = db.Column(db.DateTime, nullable=True)
    event_end_time = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    details = db.Column(db.Text, nullable=True)
    total_price = db.Column(db.Float, nullable=False, default=0.0)
    dp_paid = db.Column(db.Float, nullable=False, default=0.0)
    payment_type = db.Column(db.String(50), nullable=False, default="dp") # Kolom baru: 'dp' atau 'full'
    dp_payment_proof = db.Column(
        db.String(200), nullable=True
    )  # Path to the uploaded proof file
    status = db.Column(
        db.String(50), default="waiting_payment", nullable=False
    )  # e.g., waiting_payment, waiting_approval, accepted, rejected, completed,
    # cancellation_requested, cancelled, reschedule_requested
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    dp_rejection_timestamp = db.Column(db.DateTime, nullable=True)
    cancellation_reason = db.Column(db.Text, nullable=True)
    cancellation_requested = db.Column(
        db.Boolean, default=False, nullable=False
    )  # New field
    reschedule_reason = db.Column(db.Text, nullable=True)
    requested_event_date = db.Column(db.DateTime, nullable=True)
    requested_start_time = db.Column(db.DateTime, nullable=True)
    requested_end_time = db.Column(db.DateTime, nullable=True)
    is_notified = db.Column(
        db.Boolean, default=False, nullable=False
    )  # New field for notification
    can_submit_testimonial = db.Column(
        db.Boolean, default=False, nullable=False
    )  # New field
    is_client_hidden = db.Column(db.Boolean, default=False, nullable=False) # New field to hide order from client view
    wedding_package_id = db.Column(
        db.Integer, db.ForeignKey("wedding_package.id"), nullable=True
    )
    wedding_package = db.relationship("WeddingPackage", backref="orders")
    bank_account_id = db.Column(
        db.Integer, db.ForeignKey("bank_account.id"), nullable=True
    )
    bank_account = db.relationship("BankAccount", backref="orders")
    calendar_event = db.relationship(
        "CalendarEvent", backref="order", uselist=False, cascade="all, delete-orphan"
    )
    testimonial_submitted = db.relationship(
        "Testimonial", backref="order", uselist=False, cascade="all, delete-orphan"
    )


class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    order_id = db.Column(
        db.Integer, db.ForeignKey("order.id"), unique=True, nullable=True
    )


class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    testimonial_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)  # e.g., 1-5 stars
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_approved = db.Column(
        db.Boolean, default=False, nullable=False
    )  # Admin can approve before showing on public site
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )  # Link to User
    order_id = db.Column(
        db.Integer, db.ForeignKey("order.id"), unique=True, nullable=True
    )  # Link to Order


class WeddingPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=True, default="Wedding")  # New field


class BankAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bank_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(50), nullable=False, unique=True)
    account_name = db.Column(db.String(150), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<BankAccount {self.bank_name} - {self.account_number}>"


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )  # Admin user
    type = db.Column(
        db.String(50), nullable=False
    )  # e.g., 'new_order', 'new_client', 'new_testimonial'
    entity_id = db.Column(db.Integer, nullable=False)  # ID of the related entity
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    user = db.relationship("User", backref="notifications")

    def __repr__(self):
        return f"<Notification {self.type} - {self.message[:20]}...>"


class HomepageContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    about_text = db.Column(db.Text, nullable=False)
    about_image_filename = db.Column(db.String(150), nullable=True)

    def __repr__(self):
        return f"<HomepageContent {self.id}>"


class HeroImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    order = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<HeroImage {self.filename}>"
