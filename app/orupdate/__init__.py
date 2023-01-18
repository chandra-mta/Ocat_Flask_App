from flask import Blueprint
bp = Blueprint('orupdate', __name__)
from app.orupdate import routes
