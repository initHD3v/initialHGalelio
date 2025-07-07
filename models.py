from flask_login import UserMixin
from datetime import datetime
from extensions import db


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
    date_registered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    orders = db.relationship("Order", backref="client", lazy=True)


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


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    service_type = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    event_start_time = db.Column(db.DateTime, nullable=False)
    event_end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    details = db.Column(db.Text, nullable=True)
    total_price = db.Column(db.Float, nullable=False, default=0.0)
    dp_paid = db.Column(db.Float, nullable=False, default=0.0)
    dp_payment_proof = db.Column(
        db.String(200), nullable=True
    )  # Path to the uploaded proof file
    status = db.Column(
        db.String(50), default="waiting_dp", nullable=False
    )  # e.g., waiting_dp, waiting_approval, accepted, rejected, completed
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    dp_rejection_timestamp = db.Column(db.DateTime, nullable=True)
    is_notified = db.Column(
        db.Boolean, default=False, nullable=False
    )  # New field for notification
    can_submit_testimonial = db.Column(
        db.Boolean, default=False, nullable=False
    )  # New field
    wedding_package_id = db.Column(
        db.Integer, db.ForeignKey("wedding_package.id"), nullable=True
    )
    wedding_package = db.relationship("WeddingPackage", backref="orders")
    bank_account_id = db.Column(db.Integer, db.ForeignKey("bank_account.id"), nullable=True)
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


class BankAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bank_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(50), nullable=False, unique=True)
    account_name = db.Column(db.String(150), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<BankAccount {self.bank_name} - {self.account_number}>"
