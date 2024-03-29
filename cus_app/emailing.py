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
from cus_app.supple.ocat_common_functions   import clean_text

from email.mime.text    import MIMEText
from subprocess         import Popen, PIPE
from datetime           import datetime

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

#
#--- Cleaning step
#
    text_body = clean_text(text_body)
    subject = clean_text(subject)
    recipients = clean_text(recipients)
    if type(recipients).__name__ == 'list':
        recipients = ','.join(recipients)
    bcc = clean_text(bcc)
    if type(bcc).__name__ == 'list':
        bcc = ','.join(bcc)
    if bcc:
        message = f"To:{recipients}\nCC:{bcc}\nSubject:{subject}\n{text_body}"
        cmd = f"echo '{message}' | sendmail {recipients}"
        '''
        cmd = f"echo '{text_body}' | mailx -s '{subject}' -c '{bcc}' {recipients}"
        '''
    else:
        message = f"To:{recipients}\nSubject:{subject}\n{text_body}"
        cmd = f"echo '{message}' | sendmail {recipients}"
        '''
        cmd = f"echo '{text_body}' | mailx -s '{subject}' {recipients}"
        '''
    os.system(cmd)

#--------------------------------------------------------------
#-- send_error_email: sending out error email to admin       --
#--------------------------------------------------------------    

def send_error_email():
    handler_list = current_app.logger.handlers
    for item in handler_list:
        if item.name == "Error-Info":
            error_handler = item
            break
    file_path = error_handler.baseFilename
    #Once the log path is found, must search the file to send email contents
    with open(file_path,'r') as f:
        content = f.read()
    userinfo = []
    for k,v in current_user.__dict__.items():
        if k not in ['_sa_instance_state']:
            userinfo.append(f"({k} : {v})")
    msg = MIMEText(f"User: {' - '.join(userinfo)} \n\n ocat.log:\n{content}")
    msg["From"] = "UsintErrorHandler"
    msg["To"] = ",".join(current_app.config['ADMINS'])
    msg["Subject"] = f"Usint Error-[{datetime.now().strftime('%c')}]"
    p = Popen(["/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
    p.communicate(msg.as_bytes())


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

