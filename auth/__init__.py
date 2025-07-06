from flask import Blueprint
from . import routes  # Moved to top and explicit re-export

auth = Blueprint("auth", __name__)
