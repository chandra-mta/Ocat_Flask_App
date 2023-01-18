import os
from   datetime import timedelta
from   dotenv   import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
#
#--- loading the "environment" from .env
#
load_dotenv(os.path.join(basedir, '.env'))

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

class Config(object):

    DEBUG      = True
#
#--- application directory
#
    BASE_DIR   = os.path.abspath(os.path.dirname(__file__))
#
#--- database and csrf need secret_key
#
    SECRET_KEY = os.environ.get('SECRET_KEY')
#
#--- database
#
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
#
#--- cross-site request forgery proteciton
#
    CSRF_ENABLED    = True
    CSRF_SESSON_KEY ='some_secret-key'
#
#--- mail 
#
    MAIL_SERVER     = os.environ.get('MAIL_SERVER')
    MAIL_PORT       = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS    = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USE_SSL    = True
    MAIL_USERNAME   = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD   = os.environ.get('MAIL_PASSWORD')
    ADMINS          = ['lina.pulgarin-duque@cfa.harvard.edu']
#
#--- session activity
#
    PERMANENT_SESSION_LIFETIME   = timedelta(minutes=360)
    SESSION_REFRESH_EACH_REQUEST = True

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

class ProdConfig(Config):
    DEBUG    = False
#
#--- data directory  (MOVED TO app/static/dir_list)
#
#    OCAT_DIR  = '/data/mta4/CUS/www/Usint/ocat/'
#    INFO_DIR  = '/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/'
#    OBS_SS    = '/data/mta4/obs_ss/'
#    PASS_DIR  = '/data/mta4/CUS/www/Usint/Pass_dir/'
#    CUS_DIR   = '/data/mta4/CUS/www/Usint/'

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

class DevConfig(Config):
    ENV         = 'development'
    DEVELOPMENT = True
    SECRET_KEY  = 'secret_key_for_test'
    
    PERMANENT_SESSION_LIFETIME   = timedelta(minutes=60)
#
#--- data directory  (MOVED TO app/static/dir_list)
#
#    OCAT_DIR  = '/data/mta4/CUS/www/Usint/Ocat/ocat/Test_data/'
#    INFO_DIR  = '/data/mta4/CUS/www/Usint/Ocat/ocat/Test_data/Info_save/too_contact_info/'
#    OBS_SS    = '/data/mta4/obs_ss/'
#    PASS_DIR  = '/data/mta4/CUS/www/Usint/Pass_dir/'
#    CUS_DIR   = '/data/mta4/CUS/www/Usint/'
