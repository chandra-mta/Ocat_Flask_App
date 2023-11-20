from flask import Blueprint
bp = Blueprint('scheduler', __name__)
from cus_app.scheduler import routes
