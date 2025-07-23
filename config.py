import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or 'a_fallback_secret_key_that_is_long_and_random_for_testing'
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(basedir, "instance", "site.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
    GOOGLE_MAPS_MAP_ID = os.environ.get("GOOGLE_MAPS_MAP_ID")

    # OAuth Credentials
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID") or "326710860533-t70jp81orhb78h1ruuucqhekhfq20kh4.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET") or "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"
    FACEBOOK_CLIENT_ID = os.environ.get("FACEBOOK_CLIENT_ID")
    FACEBOOK_CLIENT_SECRET = os.environ.get("FACEBOOK_CLIENT_SECRET")


    # Konfigurasi Flask-Mail
    MAIL_SERVER = os.environ.get("MAIL_SERVER") or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    # Celery Configuration
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    CELERY_IMPORTS = ('tasks',)
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True # Added to address Celery warning
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # Hero Image Path (dynamic)
    _hero_image_config_file = os.path.join(basedir, 'instance', 'hero_image_config.txt')
    if os.path.exists(_hero_image_config_file):
        with open(_hero_image_config_file, 'r') as f:
            HERO_IMAGE_PATH = f.read().strip()
    else:
        HERO_IMAGE_PATH = os.environ.get("HERO_IMAGE_PATH") or "images/A7E00354.jpeg" # Default hero image