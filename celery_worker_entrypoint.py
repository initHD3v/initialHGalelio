from app import create_app

# Create the Flask app and get the configured Celery app
flask_app, celery_app = create_app()