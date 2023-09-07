#####################################################################################
#                                                                                   #
#       models.py:  database model for User                                         #
#                                                                                   #
#           author: t.isobe (tisobe@cfa.harvard.edu)                                #
#                                                                                   #
#           last update: May 24, 2021                                               #
#                                                                                   #
#####################################################################################
import os
import Chandra.Time
from flask              import current_app, session, request
from flask_login        import UserMixin, login_user
#from werkzeug.security  import generate_password_hash, check_password_hash
#import jwt

from app                import db, login

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

class User(UserMixin, db.Model):
    id            = db.Column(db.Integer,     primary_key=True)
    username      = db.Column(db.String(64),  index=True, unique=True)
    email         = db.Column(db.String(64),  index=True, unique=True)
    groups_string = db.Column(db.String(64),  index=True, unique=True)

    def __repr__(self):
        return '<User {}>'.format(self.username)

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

def register_user():
    session.clear()
    session['session_start'] = int(Chandra.Time.DateTime().sec)
    session.permanent = True
    session.modified = True
    #assign username, pulls from LDAP authentication login popup which is defined only in the apache server env scope
    #unless the REMOTE_USER variable is defined preemptively
    if os.getenv("FLASK_ENV") == 'development':
        if os.getenv("REMOTE_USER") != None:
            username = os.getenv("REMOTE_USER")
        else:
            username = request.environ.get("REMOTE_USER")
    else:
        username = request.environ.get("REMOTE_USER")#Similar Terminology to Apache Web Server, but assigned in Test Environment Setup
    
    user = User.query.filter_by(username=username).first()
    login_user(user)

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
