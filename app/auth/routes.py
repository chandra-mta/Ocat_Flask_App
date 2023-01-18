#####################################################################################
#                                                                                   #
#   authenticaition fucntions                                                       #
#                                                                                   #
#           author: t.isobe (tiosbe@cfa.harvard.eud)                                #
#                                                                                   #
#           last update: Jun 22, 2021                                               #
#                                                                                   #
#####################################################################################

import datetime
import time
import Chandra.Time
import random
from threading      import Thread

from flask          import render_template, redirect, url_for, flash, request, session
from flask          import Response, current_app
from werkzeug.urls  import url_parse
from flask_login    import login_user, logout_user, current_user

from app            import db
from app.auth       import bp
from app.auth.forms import LoginForm
from app.models     import User
from app.email      import send_email

import app.supple.ocat_common_functions as ocf
#
#--- create username <---> hashed password dictionary
#
user_dict = ocf.read_user()

#-----------------------------------------------------------------------------------------------
#-- login: authorization process                                                              --
#-----------------------------------------------------------------------------------------------

@bp.route('/login', methods=['GET', 'POST'])
def login():
#
#--- if the session is still active, go to the requested page.
#--- the duration of active period is defined by PERMANENT_SESSION_LIFETIME
#
    if current_user.is_authenticated:

        session['session_start'] = int(Chandra.Time.DateTime().secs)
        session.modified         = True
 
        next_page = set_the_page()
        return redirect(next_page)
#
#--- the case that login is required
#
#--- to check a brute force login attempt, sent a few parameters
#
    mchk = 0
    try:
        session['attempt'] += 1
    except:
        session['attempt']  = 1
        session['session_start'] = int(Chandra.Time.DateTime().secs)

    session.modified = True
#
#--- if the browser sends 'POST', validate_on_submit gives 'True'
#
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        error    = None
#
#--- check username is in the dict
#
        if username in user_dict.keys():
#
#--- check passowrd matches
#
            if not ocf.check_password(password, user_dict[username]):
                error = "Incorrect Password."
        else:
            error = "Username is not in the USINT user list."
#
#--- username and password matched
#
        if error is None:
#
#--- setting the session to start
#
            session.clear()
            session['session_start'] = int(Chandra.Time.DateTime().secs)
            session.permanent        = True
            session.modified         = True
#
#--- although username is read from outside of the flask system, it needs "User" 
#--- database to keep the session going. "User" database lists  id, username, and
#--- user's email address (created by update_user_database.py)
#
            user = User.query.filter_by(username=username).first()
            if user is None:
                session.pop('_flashes', None)
                flash('User name is not in USINT group!')
                return redirect(url_for('auth.login'))
#
#--- login the user for the session and go to the targeted page. 
#
            login_user(user)
            next_page = set_the_page()
            return redirect(next_page)
#
#--- username/password combination is wrong
#
        session.pop('_flashes', None)
        flash(error)
#
#--- check a broute force login attempt
#
        mchk = check_brute_force_login()
#
#--- if a potential hacking is found, sleep one hour
#
    if mchk == 1:
        time.sleep(3600)
        mchk = 0

    return render_template('auth/login.html', title='Sign In', form=form)

#-----------------------------------------------------------------------------------------------
#-- set_the_page: checking the page exsits and if so, go to the "next" page                 --
#-----------------------------------------------------------------------------------------------

def set_the_page():
    """
    checking the page exsits and whether without "https://.../" part
    if so, go to the "next" page, if not, go to main/index.html
    """
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('main.index')

    return next_page

#-----------------------------------------------------------------------------------------------
#-- check_brute_force_login: check a broute force login attempt                               --
#-----------------------------------------------------------------------------------------------

def check_brute_force_login():
    """
    if someone tries to login 5 times in less than 5 seconds, assume it 
    as a broute force login attempt. sleep 10 min
    """
#
#--- count numbers of login attempts and keep the record of login attempt time
#
    mchk = 0
    try:
        ltry = session.get('attempt')
#
#--- if someone is trying to login more than 5 times in less than 5 seconds, 
#--- assume that it is a brute force hacking attempt.
#
        if ltry >= 5:
            current = int(Chandra.Time.DateTime().secs)
            stime   = int(session.get('session_start'))
            tdiff   = current -  stime
            rate    = ltry / tdiff

            if rate > 1:
                session.pop('_flashes', None)
                flash('You exceeded login attempt limits. Try later.')
                mchk = 1
#
#--- sending alart to the admin
#
                sender  = 'cus@cfa.harvard.edu'
                address = current_app.config['ADMINS']
                subject = 'Possible Brute Force Login Atempt'
                bcc     = 'cus@cfa.harvard.edu'
                line    = 'It seems that someone is trying to login with a brute force hacking.\n\n'
                send_email(subject, sender, address, line, bcc)


            session['session_start'] = int(Chandra.Time.DateTime().secs)
            session['attempt']       = 1

    except:
        session['session_start'] = int(Chandra.Time.DateTime().secs)
        session['attempt']       = 1

    session.modified = True

    return mchk


#-----------------------------------------------------------------------------------------------
#-- logout: log out the user                                                                  --
#-----------------------------------------------------------------------------------------------

@bp.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('main.index'))

