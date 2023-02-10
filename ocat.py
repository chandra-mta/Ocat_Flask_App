import sys, os
sys.path.append('/data/mta4/CUS/www/Usint/Ocat/ocat')
sys.path.append('/data/mta4/CUS/www/Usint/Ocat/ocat/app')
os.environ.setdefault("SYBASE", "/soft/SYBASE16.0")

from app            import create_app, db       #--- in app/__init__.py
from app.models     import User

application = create_app()
#
#--- register the funion as a shell context function
#--- probably I don't need this
#
@application.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

