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
from flask              import current_app
from flask_login        import UserMixin, login_user
from werkzeug.security  import generate_password_hash, check_password_hash
import jwt

from app                import db, login

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

class User(UserMixin, db.Model):
    id            = db.Column(db.Integer,     primary_key=True)
    username      = db.Column(db.String(64),  index=True, unique=True)
    email         = db.Column(db.String(64),  index=True, unique=True)

    def __repr__(self):
        return '<User {}>'.format(self.username)

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

def register_user():
    username = 'waaron'
    #username = os.environ['REMOTE_USER'] #Depends on Apache Web Server
    user = User.query.filter_by(username=username).first()
    login_user(user)

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
