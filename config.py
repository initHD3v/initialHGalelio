import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or 'a_fallback_secret_key_that_is_long_and_random_for_testing'
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(basedir, "instance", "site.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
    GOOGLE_MAPS_MAP_ID = os.environ.get("GOOGLE_MAPS_MAP_ID")

    # Konfigurasi Flask-Mail
    MAIL_SERVER = os.environ.get("MAIL_SERVER") or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") == 'True'
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL") == 'True'
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")
