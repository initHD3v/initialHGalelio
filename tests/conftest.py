import pytest
from app import app as flask_app
from extensions import db as flask_db
from models import User, Post, PostImage, Order, CalendarEvent, Testimonial, WeddingPackage, BankAccount, Notification, HomepageContent, HeroImage
from datetime import datetime, UTC
from werkzeug.security import generate_password_hash


@pytest.fixture(scope="session")
def app():
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })

    with flask_app.app_context():
        # Create all tables once per session
        flask_db.create_all()

        # Add dummy data for HeroImage
        if not HeroImage.query.first():
            hero_image1 = HeroImage(filename="A7E00776.jpeg", order=1)
            hero_image2 = HeroImage(filename="hf.jpg", order=2)
            flask_db.session.add(hero_image1)
            flask_db.session.add(hero_image2)
            flask_db.session.commit()

        # Add dummy data for PostImage (for login/register pages)
        if not PostImage.query.first():
            dummy_post = Post(title="Dummy Post for Images", content="Content.", date_posted=datetime.now(UTC))
            flask_db.session.add(dummy_post)
            flask_db.session.commit()

            for i in range(9):
                post_image = PostImage(post_id=dummy_post.id, filename=f"dummy_image_{i}.jpg")
                flask_db.session.add(post_image)
            flask_db.session.commit()

        yield flask_app
        # Drop all tables after the session tests are done
        flask_db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        # Use nested transaction for test isolation
        connection = flask_db.engine.connect()
        transaction = connection.begin()
        flask_db.session.configure(bind=connection)

        yield flask_db

        transaction.rollback()
        connection.close()
        flask_db.session.remove()


@pytest.fixture(scope="function")
def test_user(db):
    user = User(full_name="Test User", username=f"testuser_{datetime.now().strftime('%Y%m%d%H%M%S%f')}", email=f"test_{datetime.now().strftime('%Y%m%d%H%M%S%f')}@example.com", whatsapp_number="1234567890", password=generate_password_hash("password123", method="pbkdf2:sha256"), role="client")
    db.session.add(user)
    db.session.flush()
    return user


@pytest.fixture(scope="function")
def admin_user(db):
    admin = User(full_name="Admin User", username=f"adminuser_{datetime.now().strftime('%Y%m%d%H%M%S%f')}", email=f"admin_{datetime.now().strftime('%Y%m%d%H%M%S%f')}@example.com", whatsapp_number="0987654321", password=generate_password_hash("adminpassword", method="pbkdf2:sha256"), role="admin")
    db.session.add(admin)
    db.session.flush()
    return admin