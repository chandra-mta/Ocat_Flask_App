import os
from datetime import timedelta
import binascii
from dotenv import dotenv_values
BASEDIR = os.path.abspath(os.path.dirname(__file__))
#
#--- configuration dotfiles settings
#
if os.environ.get('FLASK_RUN_FROM_CLI') == 'true':
    file_config = dotenv_values("/data/mta4/CUS/Data/Env/.localhostenv")
else:
    file_config = dotenv_values("/data/mta4/CUS/Data/Env/.cxcweb-env")

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

class Config(object):

    DEBUG      = True
    SEND_ERROR_EMAIL = file_config.get('SEND_ERROR_EMAIL') or False
    HTTP_ADDRESS = file_config.get('HTTP_ADDRESS')
#
#--- application directory
#
    BASE_DIR = BASEDIR
    LOG_DIR = os.path.join(os.path.dirname(__file__),'logs')
#
#--- database and csrf need secret_key
#
    #SECRET_KEY = file_config.get('SECRET_KEY')
    SECRET_KEY = binascii.b2a_hex(os.urandom(15)).decode()
#
#--- database
#
    SQLALCHEMY_DATABASE_URI = file_config.get('DATABASE_URL') or \
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
    MAIL_SERVER     = file_config.get('MAIL_SERVER')
    MAIL_PORT       = int(file_config.get('MAIL_PORT') or 25)
    MAIL_USE_TLS    = file_config.get('MAIL_USE_TLS') is not None
    MAIL_USE_SSL    = True
    MAIL_USERNAME   = file_config.get('MAIL_USERNAME')
    MAIL_PASSWORD   = file_config.get('MAIL_PASSWORD')
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
    SEND_ERROR_EMAIL = file_config.get('SEND_ERROR_EMAIL') or True
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
    if file_config.get('TEST_MAIL') is not None:
        TEST_MAIL = file_config.get('TEST_MAIL')
    SECRET_KEY = 'secret_key_for_test'
    PERMANENT_SESSION_LIFETIME   = timedelta(minutes=60)

    SQLALCHEMY_DATABASE_URI = 'sqlite:////data/mta4/CUS/Data/FakeUsers/app.db'
    
    #if os.path.isfile(os.path.join(BASEDIR, 'app.db')):
    #    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASEDIR, 'app.db')
        