import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or 'a_fallback_secret_key_that_is_long_and_random_for_testing'
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(basedir, "instance", "site.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_MAPS_API_KEY = (
        os.environ.get("GOOGLE_MAPS_API_KEY")
        or "AIzaSyB_j550SeE2BddmykI7NOu6uih5KPDD3I4"
    )
    GOOGLE_MAPS_MAP_ID = (
        os.environ.get("GOOGLE_MAPS_MAP_ID")
        or "AIzaSyB_j550SeE2BddmykI7NOu6uih5KPDD3I4"
    )  # Replace with your actual Map ID
    DEBUG = os.environ.get("FLASK_DEBUG") == "1"
    BABEL_DEFAULT_LOCALE = "en"
    BABEL_DEFAULT_TIMEZONE = "Asia/Jakarta"
    BABEL_TRANSLATION_DIRECTORIES = "translations"

    # Konfigurasi Flask-Mail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'arunapicturee@gmail.com'
    MAIL_PASSWORD = 'yvqg cppw cxow nzmn'
    MAIL_DEFAULT_SENDER = 'arunapicturee@gmail.com'
