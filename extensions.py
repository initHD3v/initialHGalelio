from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_babel import Babel
from flask_mail import Mail
from celery import Celery
from config import Config # Import Config directly

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
babel = Babel()
mail = Mail()

# Configure celery directly using Config object
celery = Celery(
    __name__,
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND
)
celery.conf.imports = ('tasks',)

def create_celery_app(app):
    # This function is now primarily for setting up Flask app context for tasks
    # and can optionally update config if needed, but primary config is above.
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask
    return celery
