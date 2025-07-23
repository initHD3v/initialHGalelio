from extensions import celery
from app import create_app

# This is a dummy app context for Celery to load the Flask app configuration
# It does NOT run the Flask app or register blueprints again.
flask_app = create_app()

# Configure the global celery instance with the Flask app context
# This ensures tasks can access Flask app context (e.g., db, config)
with flask_app.app_context():
    celery_app = celery