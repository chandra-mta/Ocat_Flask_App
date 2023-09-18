import os
from   datetime import timedelta
from   dotenv   import load_dotenv
import binascii

basedir = os.path.abspath(os.path.dirname(__file__))
#
#--- loading the "environment" from .env
#
if os.environ.get('FLASK_RUN_FROM_CLI') == 'true':
    load_dotenv("/data/mta4/CUS/Data/.localhostenv")
else:
    load_dotenv("/data/mta4/CUS/Data/.env")

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

class Config(object):

    DEBUG      = True
    #HTTP_ADDRESS = 'https://r2d2-v.cfa.harvard.edu/wsgi/aaron/cus/'
    HTTP_ADDRESS = os.environ.get('HTTP_ADDRESS')
#
#--- application directory
#
    BASE_DIR = basedir
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
#--- mail 
#
    MAIL_SERVER     = os.environ.get('MAIL_SERVER')
    MAIL_PORT       = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS    = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USE_SSL    = True
    MAIL_USERNAME   = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD   = os.environ.get('MAIL_PASSWORD')
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
    DEVELOPMENT = False
    OCAT_DIR = '/data/mta4/CUS/www/Usint/ocat/'
    INFO_DIR = '/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/'
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
    #SECRET_KEY  = 'secret_key_for_test'
    
    PERMANENT_SESSION_LIFETIME   = timedelta(minutes=60)
    
    if os.path.isfile(os.path.join(basedir, 'app.db')):
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
#
#--- data directory  (MOVED TO app/static/dir_list)
#
#    OCAT_DIR  = '/data/mta4/CUS/www/Usint/Ocat/ocat/Test_data/'
#    INFO_DIR  = '/data/mta4/CUS/www/Usint/Ocat/ocat/Test_data/Info_save/too_contact_info/'
#    OBS_SS    = '/data/mta4/obs_ss/'
#    PASS_DIR  = '/data/mta4/CUS/www/Usint/Pass_dir/'
#    CUS_DIR   = '/data/mta4/CUS/www/Usint/'
