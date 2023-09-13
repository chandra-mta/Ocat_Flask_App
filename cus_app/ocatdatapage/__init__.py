from flask import Blueprint
bp = Blueprint('ocatdatapage', __name__)
from cus_app.ocatdatapage import routes
