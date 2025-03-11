import os
from datetime import timedelta
import binascii


class BaseConfig(object):
    CONFIGURATION_NAME = "baseconfig"
    HTTP_ADDRESS = "http://127.0.0.1:5000"
    ADMINS = ["william.aaron@cfa.harvard.edu"]
    TEST_NOTIFICATIONS = True
    #
    # --- Database and CSRF secret key
    #
    SECRET_KEY = binascii.b2a_hex(os.urandom(15)).decode()
    #
    # --- SQLAlchemy
    #
    SQLALCHEMY_DATABASE_URI = "sqlite:////data/mta4/CUS/Data/FakeUsers/app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    #
    # --- Session Settings
    #
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    SESSION_REFRESH_EACH_REQUEST = True
    #
    # --- Directory Pathing
    #
    LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
    OBS_SS = "/data/mta4/obs_ss/"
    PASS_DIR = "/data/mta4/CUS/www/Usint/Pass_dir/"
    REV_VERSION = "test_database"
    OCAT_DIR = "/proj/web-cxc/cgi-gen/mta/Obscat/ocat/"
    INFO_DIR = "/proj/web-cxc/cgi-gen/mta/Obscat/ocat/Info_save/too_contact_info/"


class LocalHostConfig(BaseConfig):
    CONFIGURATION_NAME = "localhost"
    OBS_SS = "/data/mta4/CUS/test-database/obs_ss"
    REV_VERSION = "test_database"
    OCAT_DIR = "/data/mta4/CUS/test-database/ocat/"
    INFO_DIR = "/data/mta4/CUS/test-database/too_contact_info/"


class R2D2Config(BaseConfig):
    CONFIGURATION_NAME = "r2d2"
    HTTP_ADDRESS = "https://r2d2-v.cfa.harvard.edu/wsgi/cus/usint"
    SQLALCHEMY_DATABASE_URI = "sqlite:////data/mta4/CUS/Data/Users/app.db"


class CXCTestConfig(BaseConfig):
    CONFIGURATION_NAME = "cxctest"
    HTTP_ADDRESS = "https://cxc-test.cfa.harvard.edu/wsgi/cus/usint"
    SQLALCHEMY_DATABASE_URI = "sqlite:////data/mta4/CUS/Data/Users/app.db"


class CXCWebConfig(BaseConfig):
    CONFIGURATION_NAME = "cxcweb"
    HTTP_ADDRESS = "https://cxc.cfa.harvard.edu/wsgi/cus/usint"
    SQLALCHEMY_DATABASE_URI = "sqlite:////data/mta4/CUS/Data/Users/app.db"
    TEST_NOTIFICATIONS = False
    REV_VERSION = "live_database"
    OCAT_DIR = "/data/mta4/CUS/www/Usint/ocat/"
    INFO_DIR = "/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/"


_CONFIG_DICT = {
    'localhost': LocalHostConfig,
    'r2d2': R2D2Config,
    'cxctest': CXCTestConfig,
    'cxcweb': CXCWebConfig,
    'baseconfig': BaseConfig
}