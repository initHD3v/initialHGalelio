from flask import Blueprint
from . import routes  # Moved to top and explicit re-export

client = Blueprint("client", __name__)
