#####################################################################################
#                                                                                   #
#       setting up applications in a function                                       #
#                                                                                   #
#           author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                                   #
#           last update: Aug 13, 2021                                               #
#                                                                                   #
#####################################################################################

import os
import logging
from logging.handlers   import SMTPHandler, RotatingFileHandler

from flask              import Flask, request, current_app
from flask_sqlalchemy   import SQLAlchemy
from flask_migrate      import Migrate
from flask_login        import LoginManager
from flask_mail         import Mail
from flask_bootstrap    import Bootstrap

from config             import Config, ProdConfig, DevConfig

db                  = SQLAlchemy()
migrate             = Migrate()
login               = LoginManager()
login.login_view    = 'auth.login'
login.login_message = 'Please log in to access this page.'
mail                = Mail()
bootstrap           = Bootstrap()

#----------------------------------------------------------------------------------------
#-- create_app: setting up applications in a function                                  --
#----------------------------------------------------------------------------------------

#def create_app(config_class= ProdConfig):
def create_app(config_class= DevConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
#
#--- connect all apps with blueprint
#
#--- error handling
#
    from app.errors       import bp as errors_bp
    app.register_blueprint(errors_bp)
#
#--- authetication
#
    from app.auth         import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
#
#--- main page
#
    from app.main         import bp as main_bp
    app.register_blueprint(main_bp, url_prefix='/main')
#
#--- ocat data page
#
    from app.ocatdatapage import bp as odp_bp
    app.register_blueprint(odp_bp, url_prefix='/ocatdatapage')
#
#--- orupdate page
#
    from app.orupdate     import bp as oru_bp
    app.register_blueprint(oru_bp, url_prefix='/orupdate')
#
#--- chkupdata page
#
    from app.chkupdata    import bp as cup_bp
    app.register_blueprint(cup_bp, url_prefix='/chkupdata')
#
#--- express signoff page
#
    from app.express      import bp as exp_bp
    app.register_blueprint(exp_bp, url_prefix='/express')
#
#--- remove accidental submission page
#
    from app.rm_submission import bp as rmv_bp
    app.register_blueprint(rmv_bp, url_prefix='/rm_submission')
#
#--- poc duty sign up page
#
    from app.scheduler    import bp as sch_bp
    app.register_blueprint(sch_bp, url_prefix='/scheduler')

#
#--- if this is not a testing, setup a few other things
#
    if not app.debug and not app.testing:
#
#--- setting up the mail server connection
#
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])

            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()

            mail_handler = SMTPHandler(
            mailhost     = (app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr     = 'no-reply@' + app.config['MAIL_SERVER'],
            toaddrs      = app.config['ADMINS'], subject='Ocat Data Page Failure',
            credentials  = auth, secure=secure)

            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
#
#--- keep last 10 error logs
#
        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = RotatingFileHandler('logs/ocat.log',
                                           maxBytes=10240, backupCount=10)

        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'))

        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Ocat Data startup')

    return app
