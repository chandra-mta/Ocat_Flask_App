#########################################################################
#                                                                       #
#       error page handler                                              #
#                                                                       #
#           author: t. isobe (tisobe@cfa.harvard.edu)                   #
#                                                                       #
#           last upate: Jun 13, 2021                                    #
#                                                                       #
#########################################################################

from flask      import render_template
from cus_app        import db
from cus_app.errors import bp
from emailing       import send_error_email

#
#--- use blueprint error handler to take care the error
#
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    send_error_email()
    db.session.rollback()
    return render_template('errors/500.html'), 500
