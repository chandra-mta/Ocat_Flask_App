#################################################################################################
#                                                                                               #
#       send_notifications.py: sending notifications                                            #
#                                                                                               #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                               #
#               last update Oct 22, 2021                                                        #
#                                                                                               #
#################################################################################################

import sys
import os
import re
import math
import time
import threading
from flask_login        import current_user
from flask              import current_app

import cus_app.supple.ocat_common_functions         as ocf
import cus_app.emailing                             as email
import cus_app.ocatdatapage.create_selection_dict   as csd
#
#--- directory
#
basedir = os.path.abspath(os.path.dirname(__file__))
p_file  = os.path.join(basedir, '../static/dir_list')
with  open(p_file, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec("%s = '%s'" %(var, line))

http_address = '127.0.0.1:5000/'                #--- UPDATE UPDATE UPDATE!!!!
sender       = 'cus@cfa.harvard.edu'
bcc          = 'cus@cfa.harvard.edu'
#
#--- closing of email text
#
mail_end = '\n\nIf you have any questions about this email, please contact '
mail_end = mail_end + 'bwargelin@cfa.harvard.edu.\n'

#-----------------------------------------------------------------------------------------------
#-- send_notifications: send notificaiton email to POC, MP, ARCORP, and HRC                   --
#-----------------------------------------------------------------------------------------------

def send_notifications(asis, ct_dict, obsids_list, changed_parameters, mp_note):
    """
    send notificaiton email to POC, MP, ARCORP, and HRC
    input:  asis                --- asis status
            ct_dict             --- a dict of <paramter> <---> <information>
            obsids_list         --- a list of obdids
            changed_parameters  --- a text of a list of changed parameter values
            mp_note             --- a notificaitons to MP
    output: email sent out
    """
#
#--- find revision # for each obsids in the group
#
    o_list   = [str(ct_dict['obsid'][-1]),] + obsids_list
    rev_dict = find_rev_no(o_list)
#
#--- a standard parameter change is requsted
#
    if asis == 'norm':
#
#--- hrc si change notification
#
        if ct_dict['hrc_si_mode'][-2] != ct_dict['hrc_si_mode'][-1]:
            hrc_si_notification(obsids_list, rev_dict)
#
#--- arcops notification: multiple obsids are submitted
#
        if len(obsids_list) > 0:
            arcops_notificaiton(o_list, rev_dict, changed_parameters)
#
#--- check TOO notification
#
        send_too_notification(ct_dict, asis, rev_dict)
#
#--- mp special paramter change check
#
        check_mp_notes(mp_note, rev_dict)
#
#--- asis, remove, and clone notificaiton is simpler...
#
    elif asis in ['asis', 'remove', 'clone']:
        obsid = str(ct_dict['obsid'][-1])
        send_other_notification(asis, obsid, obsids_list)

#-----------------------------------------------------------------------------------------------
#-- hrc_si_notification: notify hrc about hrc si mode change                                 ---
#-----------------------------------------------------------------------------------------------

def hrc_si_notification(obsids_list, rev_dict):
    """
    notify hrc about hrc si mode change
    input:  obsids_list --- a list of obsids
            rev_dict    --- a dict of <obsid> <--> <revision #>
    output: email sent ot hrc
    """
    if current_app.config['DEVELOPMENT']:
        recipient = current_user.email             
    else:
        recipient = 'hrcdude@cfa.harvard.edu'

    if len(obsids_list) > 1:
        obsid   = obsids_list[0]
        subject = 'HRC SI Mode Check Requested for obsid' + obsid + ' and related obsids'
        text    = 'HRC SI Mode Check is requested for following obsids:\n\n'
        text    = text + obsid + ':  ' +  http_address + 'chkupdata/' 
        text    = text + obsid + '.'   + rev_dict[obsid] +  '\n\n'

        text    = text + 'If it is correct, please sign off at\n\n'
        text    = text + obsid + ':  ' +  http_address + 'orupdate/' 

        for end in obsids_list[1:]:
            text = text + ent + '\n'

    else:
        obsid   = obsids_list[0]
        subject = 'HRC SI Mode Check Requested for obsid' + str(obsid)
        text    = 'HRC SI Mode Check is requested for Osid: ' + str(obsid) + ':\n\n'
        text    = text + http_address + 'chkupdata/' + str(obsid) + '.' + rev_dict[obsid]  + '\n'

    text = text + mail_end

    if current_app.config['DEVELOPMENT']:
        email.send_email(subject, sender, recipient, text)
    else:
        email.send_email(subject, sender, recipient, text, bcc=bcc)

#-----------------------------------------------------------------------------------------------
#-- arcops_notificaiton: sending arcops about multiple obsid submission                       --
#-----------------------------------------------------------------------------------------------

def arcops_notificaiton(o_list, rev_dict, changed_params):
    """
    sending arcops about multiple obsid submission
    input:  o_list          --- a list of obsids
            rev_dict        --- a dict of <obsid> <--> <rev #>
            changed_param   --- a text of a list of parameter values which were updated
    output: email sent to arcorp
    """
    if current_app.config['DEVELOPMENT']:
        recipient = current_user.email
    else:
        recipient = 'arcops@cfa.harvard.edu'

    subject   = 'Multiple Obsids Are Submitted for Parameter Changes'

    text   = 'A USINT user (' + current_user.email + ') '
    text   = text + 'submitted parameter change requests to multiple obsids: \n\n'
    for ent in o_list:
        obsid = int(float(ent))
        text  = text + ent + ': ' + http_address + 'chkupdata/' 
        text  = text + ent + '.' + rev_dict[obsid] + '\n'
#
#--- change a text format to make it more readable in the email body
#
    text  = text + '\nUpdated parameters are: \n'
    text  = text + '\nParameter\t\t Original Value\t\tNew Value\n'
    text  = text + '-'* 90 + '\n'
    ctext = changed_params.replace(' to ', '\t\t :: \t\t')
    ctext = ctext.replace(' changed from ', ':     ')

    text  = text + ctext + mail_end

    if current_app.config['DEVELOPMENT']:
        email.send_email(subject, sender, recipient, text)
    else:
        email.send_email(subject, sender, recipient, text, bcc=bcc)

#-----------------------------------------------------------------------------------------------
#-- check_mp_notes: sending notification to MP                                                --
#-----------------------------------------------------------------------------------------------

def check_mp_notes(mp_note, rev_dict):
    """
    sending notification to MP
    input:  mp_note --- a list of lists of MP notification
                        [[<coordinate shift>], [obs date < 10 days], [ on OR list]]
            rev_dict    --- a dict of obsid <--> revision #
    output: email sent to MP and POC
    """
    mtext = ''                              #--- message to MP
    ptext = ''                              #--- message to POC
#
#--- large coordindate shift
#
    if len(mp_note[0]) > 0:
        msubject = 'POC requested a large coordindate shift'
        psubject = 'You submitted a large coordindate shift'

        mtext    = mtext + 'A large coordindate shift is requested in following obsid(s)\n\n'
        ptext    = ptext + 'You requested a large coordindate shift '
        ptext    = ptext + 'which requres a CDO/MP permission in following obsid(s)\n\n'

        for obsid in mp_note[0]:
            obsidrev = str(obsid) + '.' +  rev_dict[obsid]
            oline    = str(obsid)  + ': ' + http_address + 'chkupdata/' + obsidrev + '\n'
            mtext    = mtext + oline
            ptext    = ptext + oline

            rline  = obsidrev + '\n'
#
#--- keep a record of obsid.rev with a large coordindate shft so that orupdate can use it later
#
        rfile = ocat_dir + 'cdo_warning_list'

        with open(rfile, 'a') as fo:
            fo.write(rline)
#
#--- scheduled less than 10 days
#
    if len(mp_note[1]) > 0:
        for obsid in mp_note[1]:
#
#--- if the obid is in the active OR list, list it in the OR section, not here
#
            if obsid in mp_note[2]:
                continue
            else:
                msubject = 'POC requested parameter values changes on obsids scheduled in 10 days'
                psubject = 'You submitted Obsids scheduled in 10 days'

                mtext    = mtext + 'POC requested changes of parameter values in the following obsid(s) '
                mtext    = mtext + 'which are scheduled in less than 10 days.\n\n'

                ptext    = ptext + 'You requested changes of parameter values in the following obsid(s) '
                ptext    = ptext + 'which are scheduled in less than 10 days.\n\n'

                for obsid in m_note[1]:
                    oline = str(obsid)  + ': ' + http_address + 'chkupdata/' + str(obsid)
                    oline = oline + '.' + rev_dict[obsid] + '\n'
                    mtext = mtext + oline
                    ptext = ptext + oline
#
#--- on active OR list
#
    if len(mp_note[2]) > 0:
        msubject = 'POC requested parameter values changes on obsids listed on the acrive OR List'
        psubject = 'You requested parameter values changes on obsids listed on the acrive OR List'

        mtext    = mtext + 'POC requested changes of parameter values in follwoing obsid(s) ' 
        mtext    = mtext + 'which are in the active OR list.\n\n'
        ptext    = ptext + 'You requested changes of parameter values in follwoing obsid(s) ' 
        ptext    = ptext + 'which are in the active OR list.\n\n'

        for obsid in mp_note[2]:
            oline = str(obsid) + ': ' + http_address + 'chkupdata/' + str(obsid)
            oline = oline      + '.'  + rev_dict[obsid] + '\n'
            mtext = mtext + oline
            ptext = ptext + oline

        mtext = mtext + mail_end
        ptext = ptext + mail_end
#
#--- sending email to MP
#
    if mtext != '':
        if current_app.config['DEVELOPMENT']:
            recipient = current_user.email 
            email.send_email(msubject, sender, recipient, mtext)

        else:
            recipient = 'mp@cfa.harvard.edu'
            email.send_email(msubject, sender, recipient, mtext, bcc=bcc)
#
#--- sending email to POC
#
    if ptext != '':
        recipient = current_user.email 
        ptext     = ptext + '\n\n Please constact mp@cfa.harvard.edu, if you have not done so.\n\n'

        if current_app.config['DEVELOPMENT']:
            email.send_email(psubject, sender, recipient, ptext)
        else:
            email.send_email(psubject, sender, recipient, ptext, bcc=bcc)

#-----------------------------------------------------------------------------------------------
#-- send_other_notification: send a short notification for asis, remove, and clone case       --
#-----------------------------------------------------------------------------------------------

def send_other_notification(asis, obsid, obsids_list):
    """
    send a short notification for asis, remove, and clone case
    input:  asis        --- asis, remove, or clone
            obsid       ---  the main obsid
            obsids_list --- a list of obsids
    output: email sent to POC
    """
    recipient = current_user.email

    chk = 0
    if len(obsids_list) > 0:
        subject = obsid + ' and related obsids are submitted as ' + asis
        chk = 1
    else:
        subject = obsid + ' is subimitted as ' + asis

    if asis == 'asis':
        if chk == 0:
            text = obsid + ' is approved. Thank you.\n'
        else:
            text = 'The following obsids are approved. Thank you.\n\n'
            text = text + obsid + '\n'
            for ent in obsids_list:
               text = text + ent + '\n' 

    elif asis == 'remove':
        if chk == 0:
            text = obsid + ' is removed from the approved list.\n'
        else:
            text = 'The following obsids are removed from the approved list.\n\n'
            text = text + obsid + '\n'
            for ent in obsids_list:
               text = text + ent + '\n' 

    elif asis == 'clone':
        text = 'A split request for ' + obsid + ' is submitted.\n'

    text = text + mail_end

    if current_app.config['DEVELOPMENT']:
        email.send_email(subject, sender, recipient, text)
    else:
        email.send_email(subject, sender, recipient, text, bcc=bcc)

#-----------------------------------------------------------------------------------------------
#-- send_too_notification: notify arcops about a fast too observation parameter update        --
#-----------------------------------------------------------------------------------------------

def send_too_notification(ct_dict, asis, rev_dict):
    """
    notify arcops about a fast too observation parameter update
    input:  ct_dict     --- dict of <param> <---> <informaiton>
            asis        --- submission station
            rev_dict    --- a dict of <obsid> <---> <rev #>
    output: email sent to arcops
    """
#
#--- assume that if the too type is 0-5, it is a fast TOO observation
#
    if (ct_dict['too_type'][-1] == '0-5') and (asis == 'norm'):
        obsid = ct_dict['obsid'][-1]
        otype = ct_dict['type'][-1]

        text  = otype.upper() + ' observation ' + str(obsid) + ' parameter updates were ' 
        text  = text + 'submitted.\n\n'

        text  = text + '\tTOO ID:     ' + ct_dict['tooid'][-1]       + '\n'
        text  = text + '\tTOO Type:   ' + ct_dict['too_type'][-1]    + '\n'
        text  = text + '\tTOO Tigger: ' + ct_dict['too_trig'][-1]    + '\n'
        text  = text + '\tREMARKS:    ' + ct_dict['too_remarks'][-1] + '\n\n\n'
        text  = text + http_address + 'chkupdata/' + str(obsid) + '.' + rev_dict[obsid]  + '\n'
        text  = text + mail_end
 
        subject = otype.upper() + ' observation ' + str(obsid) + ' parameter updates'

        if current_app.config['DEVELOPMENT']:
            recipient = current_user.email
            email.send_email(subject, sender, recipient, text)
        else:
            recipient = 'arcops@cfa.harvard.edu'
            email.send_email(subject, sender, recipient, text, bcc=bcc)

#-----------------------------------------------------------------------------------------------
#-- find_rev_no: create a dict of obsid <--> updated revision #                              ---
#-----------------------------------------------------------------------------------------------

def find_rev_no(o_list):
    """
    create a dict of obsid <--> updated revision #
    input:  o_list      --- a list of obsids
    output: rev_dict    --- a dict of <obsid> <--> <updated revision #>
    """
    ifile = ocat_dir  + 'updates_table.list'
    data  = ocf.read_data_file(ifile)

    rev_dict = {}
    for ent in data:
        atemp = re.split('\s+', ent)
        btemp = re.split('\.',  atemp[0])
        if btemp[0] in o_list:
            obsid = int(float(btemp[0]))
            rev   = int(float(btemp[1]))
            if obsid in rev_dict.keys():
                prev = rev_dict[obsid]
                if prev < rev:
                    rev_dict[obsid] = rev
            else:
                rev_dict[obsid] = rev

    for obsid in o_list:
        obsid = int(obsid)
        if obsid in rev_dict.keys():
            rev = rev_dict[obsid] 
            rev = ocf.add_leading_zero(rev, 3)
            rev_dict[obsid] = rev

        else:
            rev_dict[obsid] = '001'

    return rev_dict

