#############################################################################
#                                                                           #
#           sending out email                                               #
#                                                                           #
#               author: t. isobe (tisobe@cfa.harvard.eud)                   #
#                                                                           #
#               last upate: Aug 17, 2021                                    #
#                                                                           #
#############################################################################

import os
import time

from threading      import Thread               #--- setting for asynchormous email
from flask          import current_app
from flask_mail     import Message
from flask_login    import current_user
from cus_app            import mail

cus  = 'cus@cfa.harvard.edu'

#--------------------------------------------------------------
#-- send_email: sending out email                           ---
#--------------------------------------------------------------

def send_email(subject, sender, recipients, text_body, bcc=''):
    """
    sending out email
    input:  subject     --- subject
            sender      --- sender email address: not used in this function
            recipients  --- email address of recipient(s)
            text_body   --- email text
            bcc         --- bcc email address. default ""
    output: email sent out
    """
#
#--- if this is a test say so
#
    if current_app.config['DEVELOPMENT']:
        subject    = 'TEST!!!: ' + subject 
        cus        = None
        recipients = current_user.email
        if bcc != '':
            bcc    = current_user.email
    
    if bcc:
        cmd = f"echo '{text_body}' | mailx -s '{subject}' -c '{bcc}' {recipients}"
    else:
        cmd = f"echo '{text_body}' | mailx -s '{subject}' {recipients}"
    os.system(cmd)
    
#-------------------------------------------------------------
#-- CURRENTLY NOT USED!!! -------------------------------------
#--------------------------------------------------------------

def send_email_xxx(subject, sender, recipients, text_body, bcc=cus):
#
#--- if bcc is not None, add bcc (usually sending to cus)
#
    if bcc:
        msg      = Message(subject, sender=sender, recipients=recipients, bcc=bcc)
    else:
        msg      = Message(subject, sender=sender, recipients=recipients)

    msg.body = text_body
    msg.html = ''
#
#--- run the email process in background
#--- _get_current_object: extract the actual application instacne from insdie the proxy obj
#
    Thread(target=send_async_email,
           args=(current_app._get_current_object(), msg)).start()

#--------------------------------------------------------------
#--------------------------------------------------------------
#--------------------------------------------------------------

def send_async_email(app, msg):

    with app.app_context():
        mail.send(msg)

