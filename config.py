import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///site.db"
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
