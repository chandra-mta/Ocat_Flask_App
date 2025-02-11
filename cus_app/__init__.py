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
from logging.handlers import RotatingFileHandler
from flask import Flask, request, current_app, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from config import _CONFIG_DICT

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()
bootstrap = Bootstrap()


# ----------------------------------------------------------------------------------------
# -- create_app: setting up applications in a function                                  --
# --------------------------------------------------------------------   --------------------
# def create_app(config_class=ProdConfig):
def create_app(_configuration_name):
    app = Flask(__name__)
    app.config.from_object(_CONFIG_DICT[_configuration_name])
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    #
    # --- connect all apps with blueprint
    #
    # --- error handling
    #
    from cus_app.errors import bp as errors_bp

    app.register_blueprint(errors_bp)

    #
    # --- ocat data page
    #
    from cus_app.ocatdatapage import bp as odp_bp

    app.register_blueprint(odp_bp, url_prefix="/ocatdatapage")
    #
    # --- orupdate page
    #
    from cus_app.orupdate import bp as oru_bp

    app.register_blueprint(oru_bp, url_prefix="/orupdate")
    #
    # --- chkupdata page
    #
    from cus_app.chkupdata import bp as cup_bp

    app.register_blueprint(cup_bp, url_prefix="/chkupdata")
    #
    # --- express signoff page
    #
    from cus_app.express import bp as exp_bp

    app.register_blueprint(exp_bp, url_prefix="/express")
    #
    # --- remove accidental submission page
    #
    from cus_app.rm_submission import bp as rmv_bp

    app.register_blueprint(rmv_bp, url_prefix="/rm_submission")
    #
    # --- poc duty sign up page
    #
    from cus_app.scheduler import bp as sch_bp

    app.register_blueprint(sch_bp, url_prefix="/scheduler")

    #
    # --- Main Usint Page
    #
    @app.route("/")
    def index():
        return render_template("index.html")

    #
    # --- Setup file logger for UsintErrorHandler if not using the Werkzeug Browser Debugger
    #
    if not app.debug:
        #
        # --- keep last 10 error logs
        #
        if not os.path.exists(app.config["LOG_DIR"]):
            os.mkdir(app.config["LOG_DIR"])
        file_handler = RotatingFileHandler(
            os.path.join(app.config["LOG_DIR"], "ocat.log"),
            maxBytes=10240,
            backupCount=10,
        )
        file_handler.name = "Error-Info"
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s " "[in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
    return app
