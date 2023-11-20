from flask import Blueprint
bp = Blueprint('chkupdata', __name__)
from cus_app.chkupdata import routes
