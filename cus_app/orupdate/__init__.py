from flask import Blueprint
bp = Blueprint('orupdate', __name__)
from cus_app.orupdate import routes
