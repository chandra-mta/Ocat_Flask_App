from flask import Blueprint
bp = Blueprint('rm_submission', __name__)
from cus_app.rm_submission import routes
