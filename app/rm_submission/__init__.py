from flask import Blueprint
bp = Blueprint('rm_submission', __name__)
from app.rm_submission import routes
