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
from flask          import current_app
from flask_login    import current_user
from cus_app            import mail
from cus_app.supple.ocat_common_functions   import clean_text

from email.mime.text    import MIMEText
from subprocess         import Popen, PIPE
from datetime           import datetime

CUS  = 'cus@cfa.harvard.edu'

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
    cus = CUS
#
#--- if this is a test say so
#
    if current_app.config['DEVELOPMENT']:
        subject    = 'TEST!!!: ' + subject 
        cus        = ''
        recipients = current_user.email
        bcc    = ''

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
    if cus != '':
        if bcc != '':
            bcc = f"{bcc},{cus}"
        else:
            bcc = cus

    if bcc:
        message = f"To:{recipients}\nCC:{bcc}\nSubject:{subject}\n{text_body}"
        cmd = f"echo '{message}' | sendmail {recipients}"
    else:
        message = f"To:{recipients}\nSubject:{subject}\n{text_body}"
        cmd = f"echo '{message}' | sendmail {recipients}"
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


#--------------------------------------------------------------
#--------------------------------------------------------------
#--------------------------------------------------------------

def send_async_email(app, msg):

    with app.app_context():
        mail.send(msg)

