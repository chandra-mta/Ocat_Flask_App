#################################################################################################
#                                                                                               #
#       send_notifications.py: sending notifications                                            #
#                                                                                               #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                               #
#               last update Oct 22, 2021                                                        #
#                                                                                               #
#################################################################################################
import os
import re
from flask_login        import current_user
from flask              import current_app
import cus_app.emailing                             as email

sender       = 'cus@cfa.harvard.edu'
#
#--- closing of email text
#
mail_end = 'If you have any questions about this email, please contact bwargelin@cfa.harvard.edu.\n'

#-----------------------------------------------------------------------------------------------
#-- send_notifications: send notification email to POC, MP, ARCOPS, and HRC                   --
#-----------------------------------------------------------------------------------------------

def send_notifications(asis, ct_dict, obsids_list, changed_parameters, mp_note):
    """
    send notification email to POC, MP, ARCORP, and HRC
    input:  asis                --- asis status
            ct_dict             --- a dict of <parameter> <---> <information>
            obsids_list         --- a list of additional obsids
            changed_parameters  --- a text of a list of changed parameter values
            mp_note             --- a notifications to MP
    output: email sent out
    """
#
#--- find revision # for each obsids in the group
#--- obsids as keys and values are all set as integer types by default
#
    o_list   = [ct_dict['obsid'][-1]] + [int(x) for x in obsids_list]
    rev_dict = find_rev_no(o_list)
#
#--- a standard parameter change is requsted
#
    if asis == 'norm':
#
#--- hrc si change notification
#
        if ct_dict['hrc_si_mode'][-2] != ct_dict['hrc_si_mode'][-1]:
            hrc_si_notification(o_list, rev_dict)
#
#--- arcops notification: multiple obsids are submitted
#
        if len(o_list) > 1:
            arcops_notification(o_list, rev_dict, changed_parameters)
#
#--- check TOO notification
#
        send_too_notification(ct_dict, asis, rev_dict)
#
#--- mp special parameter change check
#
        check_mp_notes(mp_note, rev_dict)
#
#--- remove, and clone notification is simpler...
#--- for convenience, intakes the obsid and obsids_list values as strings
#
    elif asis in ['remove', 'clone']:
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
    output: email sent to hrc
    """
    recipient = 'hrcdude@cfa.harvard.edu'

    if len(obsids_list) > 1:
        obsid   = obsids_list[0]
        subject = f'HRC SI Mode Check Requested for Obsid {obsid} and related obsids'
        text    = 'HRC SI Mode Check is requested for the following obsids:\n\n'
        for ent in obsids_list:
            text += f"{ent}: {current_app.config['HTTP_ADDRESS']}/chkupdata/{ent}.{rev_dict[ent]}\n"

        text += '\nIf these are correct, please sign off at\n\n'
        text += f"{current_app.config['HTTP_ADDRESS']}/orupdate/"

    else:
        obsid   = obsids_list[0]
        subject = f'HRC SI Mode Check Requested for Obsid {obsid}'
        text    = f'HRC SI Mode Check is requested for Obsid: \n\n {obsid}:'
        text    += f"{current_app.config['HTTP_ADDRESS']}/chkupdata/{obsid}.{rev_dict[obsid]}\n"

        text += 'If this is correct, please sign off at\n\n'
        text += f"{current_app.config['HTTP_ADDRESS']}/orupdate/"

    text = text + "\n\n" + mail_end
    email.send_email(subject, sender, recipient, text)

#-----------------------------------------------------------------------------------------------
#-- arcops_notification: sending arcops about multiple obsid submission                       --
#-----------------------------------------------------------------------------------------------

def arcops_notification(o_list, rev_dict, changed_params):
    """
    sending arcops about multiple obsid submission
    input:  o_list          --- a list of obsids
            rev_dict        --- a dict of <obsid> <--> <rev #>
            changed_param   --- a text of a list of parameter values which were updated
    output: email sent to arcops
    """
    recipient = 'arcops@cfa.harvard.edu'
    subject   = 'Multiple Obsids Are Submitted for Parameter Changes'

    text   = f'A USINT user ({current_user.email}) submitted parameter change requests to multiple obsids: \n\n'
    for ent in o_list:
        text += f"{ent}: {current_app.config['HTTP_ADDRESS']}/chkupdata/{ent}.{rev_dict[ent]}\n"
#
#--- change a text format to make it more readable in the email body
#
    text += f'\nUpdated parameters for {o_list[0]} are: \n'
    text += '\nParameter\t\t Original Value\t\tNew Value\n'
    text += '-'* 90 + '\n'
    ctext = changed_params.replace(' to ', '\t\t :: \t\t')
    ctext = ctext.replace(' changed from ', ':     ')

    text += f"{ctext}\n\n{mail_end}"
    email.send_email(subject, sender, recipient, text)

#-----------------------------------------------------------------------------------------------
#-- check_mp_notes: sending notification to MP                                                --
#-----------------------------------------------------------------------------------------------

def check_mp_notes(mp_note, rev_dict):
    """
    sending notification to MP
    input:  mp_note --- a dictionary of MP notification information
                        keyed by targname_change, coordinate_shift, obsdate_under10, on_or_list
            rev_dict    --- a dict of obsid <--> revision #
    output: email sent to MP and POC
    """
    mtext = ''                              #--- message to MP
    msubject = f'POC {current_user.username} submitted a request which requires MP attention'
#
#--- target name change
#
    if 'targname_change' in mp_note.keys():
        mtext += "A target name change was requested for the following obsid(s)\n\n"

        for obsid in mp_note['targname_change']:
            obsidrev = f"{obsid}.{rev_dict[obsid]}"
            oline = f"{obsid}: {current_app.config['HTTP_ADDRESS']}/chkupdata/{obsidrev}\n"
            mtext += f"{oline}"
        mtext += f"{'-'*70}\n\n"
#
#--- large coordinate shift
#
    if 'coordinate_shift' in mp_note.keys():
        rline = ''
        mtext += "A coordinate shift was requested for the following obsid(s)\n\n"

        for obsid in mp_note['coordinate_shift']:
            obsidrev = f"{obsid}.{rev_dict[obsid]}"
            oline = f"{obsid}: {current_app.config['HTTP_ADDRESS']}/chkupdata/{obsidrev}\n"
            mtext += f"{oline}"
            rline += obsidrev + '\n'
        mtext += f"{'-'*70}\n\n"
        with open(os.path.join(current_app.config['OCAT_DIR'], 'cdo_warning_list'), 'a') as fo:
            fo.write(rline)
#
#--- scheduled less than 10 days
#
    if 'obsdate_under10' in mp_note.keys():
        subsection = ''
        for obsid in mp_note['obsdate_under10']:
#
#--- if the obsid is in the active OR list, list it in the OR section, not here
#
            if 'on_or_list' in mp_note.keys():
                if obsid in mp_note['on_or_list']:
                    continue
            obsidrev = f"{obsid}.{rev_dict[obsid]}"
            oline = f"{obsid}: {current_app.config['HTTP_ADDRESS']}/chkupdata/{obsidrev}\n"
            subsection += f"{oline}"
        
        if subsection != '':
            mtext += f"A parameter change was requested for the following obsid(s) which are scheduled in less than 10 days\n\n {subsection}"
            mtext += f"{'-'*70}\n\n"
#
#--- on active OR list
#
    if 'on_or_list' in mp_note.keys():
        mtext += "A target name change was requested for the following obsid(s)\n\n"

        for obsid in mp_note['on_or_list']:
            obsidrev = f"{obsid}.{rev_dict[obsid]}"
            oline = f"{obsid}: {current_app.config['HTTP_ADDRESS']}/chkupdata/{obsidrev}\n"
            mtext += f"{oline}"
        mtext += f"{'-'*70}\n\n"
#
#--- sending email to MP
#
    if mtext != '':
        mtext += f"{mail_end}"
        recipient = 'mp@cfa.harvard.edu'
        bcc = current_user.email
        email.send_email(msubject, sender, recipient, mtext, bcc = bcc)

#-----------------------------------------------------------------------------------------------
#-- send_other_notification: send a short notification for asis, remove, and clone case       --
#-----------------------------------------------------------------------------------------------

def send_other_notification(asis, obsid, obsids_list):
    """
    send a short notification for remove, and clone case
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
        subject = obsid + ' is submitted as ' + asis

    if asis == 'remove':
        if chk == 0:
            text = obsid + ' is removed from the approved list.\n'
        else:
            text = 'The following obsids are removed from the approved list.\n\n'
            text = text + obsid + '\n'
            for ent in obsids_list:
               text = text + ent + '\n' 

    elif asis == 'clone':
        text = 'A split request for ' + obsid + ' is submitted.\n'

    text = text + "\n\n" + mail_end
    email.send_email(subject, sender, recipient, text)

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
        text  = text + current_app.config['HTTP_ADDRESS'] + '/chkupdata/' + str(obsid) + '.' + rev_dict[obsid]  + '\n'
        text  = text + "\n\n" + mail_end
 
        subject = otype.upper() + ' observation ' + str(obsid) + ' parameter updates'
        recipient = 'arcops@cfa.harvard.edu'
        email.send_email(subject, sender, recipient, text)

#-----------------------------------------------------------------------------------------------
#-- find_rev_no: create a dict of obsid <--> updated revision #                              ---
#-----------------------------------------------------------------------------------------------

def find_rev_no(o_list):
    """
    create a dict of obsid <--> updated revision #
    input:  o_list      --- a list of obsids
    output: rev_dict    --- a dict of <obsid> <--> <updated revision #>
    """
    ifile = os.path.join(current_app.config['OCAT_DIR'], 'updates_table.list')
    with open(ifile) as f:
        data = [line.strip() for line in f.readlines()]

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
            rev = f"{rev_dict[obsid]:>03}"
            rev_dict[obsid] = rev

        else:
            rev_dict[obsid] = '001'

    return rev_dict

