from flask import Blueprint
bp = Blueprint('main', __name__)
from cus_app.main import routes
