from models import User, Post, PostImage
from datetime import datetime, UTC

def test_new_user(db):
    user = User(full_name="Test User", username="testuser", email="test@example.com", whatsapp_number="1234567890", password="hashedpassword", role="client")
    db.session.add(user)
    db.session.commit()
    assert user.id is not None
    assert user.username == "testuser"

def test_new_post(db):
    post = Post(title="Test Post", content="This is a test post.", date_posted=datetime.now(UTC))
    db.session.add(post)
    db.session.commit()
    assert post.id is not None
    assert post.title == "Test Post"

def test_new_post_image(db):
    post = Post(title="Image Post", content="Content.", date_posted=datetime.now(UTC))
    db.session.add(post)
    db.session.commit()

    image = PostImage(post_id=post.id, filename="test_image.jpg")
    db.session.add(image)
    db.session.commit()
    assert image.id is not None
    assert image.filename == "test_image.jpg"
    assert image.post.id == post.id
