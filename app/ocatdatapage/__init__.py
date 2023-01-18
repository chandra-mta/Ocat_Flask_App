from flask import Blueprint
bp = Blueprint('ocatdatapage', __name__)
from app.ocatdatapage import routes
