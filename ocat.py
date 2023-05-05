import sys, os
#For finding the Application scripts in directory where the ocat.py script is located
sys.path.insert(0,f"{os.path.dirname(os.path.realpath(__file__))}")
sys.path.insert(1,f"{os.path.dirname(os.path.realpath(__file__))}/app")

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

