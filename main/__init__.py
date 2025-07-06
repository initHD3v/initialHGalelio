from flask import Blueprint
from . import routes  # Moved to top and explicit re-export

main = Blueprint("main", __name__)
