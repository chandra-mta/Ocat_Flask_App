#############################################################################
#                                                                           #
#   create main usint ocat home page                                        #
#                                                                           #
#       author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                           #
#       last update: Aug 13, 2021                                           #
#                                                                           #
#############################################################################

import os
from datetime       import datetime
from flask          import render_template, flash, redirect, url_for 
from flask          import request, g, jsonify, current_app
from flask_login    import current_user, login_required, login_user

from app            import db
from app.main.forms import EmptyForm
from app.models     import User, register_user
from app.main       import bp
#----------------------------------------------------------------------------------
#-- before_request: this will be run before every time index is called          ---
#----------------------------------------------------------------------------------

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    else:
        register_user()

#----------------------------------------------------------------------------------
#-- index: this is the main function to dispaly main page                        --
#----------------------------------------------------------------------------------

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
#@login_required
def index():
    return render_template('index.html')


