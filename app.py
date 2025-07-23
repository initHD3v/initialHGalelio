from flask import Flask, request, session, flash, render_template
from dotenv import load_dotenv
from config import Config # Import Config
from extensions import db, login_manager, mail, migrate, babel, create_celery_app
from models import User, Post, PostImage, Order, CalendarEvent, Testimonial, WeddingPackage, BankAccount, Notification, HomepageContent, HeroImage
from werkzeug.security import generate_password_hash
import os
from datetime import datetime, UTC
from flask_babel import _  # Import _ function

# Load environment variables from .env file
load_dotenv()

# Import blueprints here to avoid circular imports
from auth import auth
from admin import admin
from main import main
from client import client



def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    @app.context_processor
    def inject_datetime():
        from datetime import datetime
        return dict(datetime=datetime)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app)

    # Inisialisasi Celery
    celery_app = create_celery_app(app)
    mail.init_app(app)
    login_manager.login_view = "auth.login"

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(main)
    app.register_blueprint(client)

    @app.context_processor
    def inject_google_maps_api_key():
        return dict(google_maps_api_key=app.config["GOOGLE_MAPS_API_KEY"])

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    return app, celery_app # Return both app and celery_app


def get_locale():
    if request.args.get("lang"):
        session["lang"] = request.args.get("lang")
    return session.get("lang", "en")


if __name__ == "__main__":
    # The app.run() call is only for local development and will now respect
    # the FLASK_DEBUG environment variable.
    app, celery_app = create_app() # Create app and get celery_app instance
    is_debug = app.config.get("DEBUG", False)
    
    app.run(debug=is_debug, host="0.0.0.0", port=5001)
