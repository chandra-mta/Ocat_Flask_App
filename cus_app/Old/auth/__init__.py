from flask import Blueprint
bp = Blueprint('auth', __name__)
from cus_app.auth import routes

