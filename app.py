from flask import Flask, request, session
from dotenv import load_dotenv
from extensions import db, login_manager, migrate, babel
from models import User, Post, PostImage
from werkzeug.security import generate_password_hash
import click
import os
import random
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Import blueprints here to avoid circular imports
from auth import auth
from admin import admin
from main import main
from client import client

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None
    print(
        "Pillow is not installed. Please install it using 'pip install Pillow' "
        "to generate dummy images."
    )

app = Flask(__name__)
app.config.from_object("config.Config")
db.init_app(app)
login_manager.init_app(app)
migrate.init_app(app, db)
babel.init_app(app)
login_manager.login_view = "auth.login"

app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(main)
app.register_blueprint(client)


@babel.localeselector
def get_locale():
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    return session.get('lang', 'en')


@app.context_processor
def inject_google_maps_api_key():
    return dict(google_maps_api_key=app.config["GOOGLE_MAPS_API_KEY"])


@app.cli.command("create-admin")
@click.argument("username")
@click.argument("password")
def create_admin(username, password):
    """Create a new admin user."""
    hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
    admin = User(
        full_name="Admin User",
        username=username,
        email=f"{username}@example.com",
        whatsapp_number="0000000000",
        password=hashed_password,
        role="admin",
    )
    with app.app_context():
        db.session.add(admin)
        db.session.commit()
    print(f"Admin user {username} created successfully.")


@app.cli.command("generate-dummy-portfolio")
@click.argument("num_posts", default=5, type=int)
@click.argument("images_per_post", default=3, type=int)
def generate_dummy_portfolio(num_posts, images_per_post):
    """Generate dummy portfolio posts and images."""
    if Image is None:
        print(
            "Pillow is not installed. Cannot generate dummy images. "
            "Please install it using 'pip install Pillow'."
        )
        return

    image_dir = os.path.join(app.root_path, "static", "images")
    os.makedirs(image_dir, exist_ok=True)

    with app.app_context():
        print(
            f"Generating {num_posts} dummy posts with {images_per_post} images each..."
        )
        for i in range(num_posts):
            title = f"Dummy Post {i+1}"
            content = ("This is dummy content for post {i+1}. It showcases some of "
                       "our amazing work.")
            post = Post(title=title, content=content, date_posted=datetime.utcnow())
            db.session.add(post)
            db.session.flush()  # To get post.id before committing

            for j in range(images_per_post):
                filename = f"dummy_image_{i+1}_{j+1}.png"
                filepath = os.path.join(image_dir, filename)

                # Generate dummy image
                img_size = (400, 300)
                img = Image.new(
                    "RGB",
                    img_size,
                    color=(
                        random.randint(0, 255),
                        random.randint(0, 255),
                        random.randint(0, 255),
                    ),
                )
                d = ImageDraw.Draw(img)
                try:
                    # Try to load a default font, or use a generic one
                    font = ImageFont.truetype("arial.ttf", 30)
                except IOError:
                    font = ImageFont.load_default()

                text = f"Image {j+1}"
                # Use textbbox for modern Pillow versions
                bbox = d.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (img_size[0] - text_width) / 2
                y = (img_size[1] - text_height) / 2
                d.text((x, y), text, fill=(255, 255, 255), font=font)
                img.save(filepath)

                post_image = PostImage(post_id=post.id, filename=filename)
                db.session.add(post_image)

        db.session.commit()
        print("Dummy portfolio data generated successfully!")


if __name__ == "__main__":
    # The app.run() call is only for local development and will now respect
    # the FLASK_DEBUG environment variable.
    is_debug = app.config.get("DEBUG", False)
    with app.app_context():
        db.create_all()
    app.run(debug=is_debug, host="0.0.0.0", port=5001)
