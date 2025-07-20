from app import create_app
from extensions import celery, create_celery_app

# Create the Flask app context
flask_app = create_app()

# Configure the global celery instance with the Flask app context
celery_app = create_celery_app(flask_app)
