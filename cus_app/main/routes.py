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
from flask_login    import current_user

from cus_app            import db
from cus_app.main.forms import EmptyForm
from cus_app.models     import User, register_user
from cus_app.main       import bp
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
def index():
    return render_template('index.html')


