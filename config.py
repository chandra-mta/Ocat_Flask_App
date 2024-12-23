import os
from datetime import timedelta
import binascii
BASEDIR = os.path.abspath(os.path.dirname(__file__))

#os.environ should be filled with environment variables in the calling flask app creation script which calls the config object.

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

class Config(object):

    DEBUG      = True
    SEND_ERROR_EMAIL = os.environ.get('SEND_ERROR_EMAIL') or False
    HTTP_ADDRESS = os.environ.get('HTTP_ADDRESS')
#
#--- application directory
#
    BASE_DIR = BASEDIR
    LOG_DIR = os.path.join(os.path.dirname(__file__),'logs')
#
#--- database and csrf need secret_key
#
    #SECRET_KEY = os.environ.get('SECRET_KEY')
    SECRET_KEY = binascii.b2a_hex(os.urandom(15)).decode()
#
#--- database
#
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:////data/mta4/CUS/Data/Users/app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
#
#--- cross-site request forgery protection
#
    CSRF_ENABLED    = True
    #CSRF_SESSON_KEY ='some_secret-key'
#
#--- mail (SMTPHandler future implementation)
#
    MAIL_SERVER     = os.environ.get('MAIL_SERVER')
    MAIL_PORT       = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS    = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USE_SSL    = True
    MAIL_USERNAME   = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD   = os.environ.get('MAIL_PASSWORD')
    TEST_MAIL       = False
    ADMINS          = ['william.aaron@cfa.harvard.edu']
#
#--- session activity
#
    PERMANENT_SESSION_LIFETIME   = timedelta(minutes=360)
    SESSION_REFRESH_EACH_REQUEST = True

#
#--- directory listing - dev default
#
    
    OCAT_DIR = '/proj/web-cxc/cgi-gen/mta/Obscat/ocat/'
    OBS_SS = '/data/mta4/obs_ss/'
    CUS_DIR = '/data/mta4/CUS/www/Usint/'
    PASS_DIR = '/data/mta4/CUS/www/Usint/Pass_dir/'
    INFO_DIR = '/proj/web-cxc/cgi-gen/mta/Obscat/ocat/Info_save/too_contact_info/'


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

class ProdConfig(Config):
    DEBUG    = False
    SEND_ERROR_EMAIL = os.environ.get('SEND_ERROR_EMAIL') or True
    DEVELOPMENT = False
#
#--- Live Directory Settings
#
    OCAT_DIR = '/data/mta4/CUS/www/Usint/ocat/'
    INFO_DIR = '/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/'


#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

class DevConfig(Config):
    ENV         = 'development'
    DEVELOPMENT = True
    if os.environ.get('TEST_MAIL') is not None:
        TEST_MAIL = os.environ.get('TEST_MAIL')
    SECRET_KEY = 'secret_key_for_test'
    PERMANENT_SESSION_LIFETIME   = timedelta(minutes=60)

    SQLALCHEMY_DATABASE_URI = 'sqlite:////data/mta4/CUS/Data/FakeUsers/app.db'
    
    #if os.path.isfile(os.path.join(BASEDIR, 'app.db')):
    #    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASEDIR, 'app.db')
        