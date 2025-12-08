#################################################################################################
#                                                                                               #
#       update_data_record_file.py: create a data recorde file for a given obsid                #
#                                                                                               #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                               #
#               last update Sep 21, 2021                                                        #
#                                                                                               #
#################################################################################################

import sys
import os
import re
import math
import time
import Chandra.Time
import sqlite3 as sq
from contextlib import closing
import traceback
import threading
from flask          import flash, current_app, abort
from flask_login    import current_user

import cus_app.supple.ocat_common_functions         as ocf
import cus_app.emailing                             as email
import cus_app.ocatdatapage.create_selection_dict   as csd
#
#--- directory
#
basedir = os.path.abspath(os.path.dirname(__file__))
null_list = [None, 'NA', 'N', 'NULL', 'None', 'NONE',  'n', 'null', 'none', '', ' ']
skip_list = ['monitor_series', 'obsids_list', 'remarks', 'comments', 'approved',\
             'group_obsid', 'dec', 'ra', 'acis_open', 'hrc_open']

now       = Chandra.Time.DateTime().secs

ARCOPS = "arcops@cfa.harvard.edu"

#-----------------------------------------------------------------------------------------------
#-- update_data_record_file: create a data recorde file for a given obsid                    ---
#-----------------------------------------------------------------------------------------------

def update_data_record_file(ct_dict, ind_dict, asis, user):
    """
    create a data recorde file for a given obsid
    input:  ct_dict     --- a dict of <param> <---> <information>
            ind_dict    --- a dict of <param> <---> <0/1> 0: value changed/1: value is same
            asis        --- asis status
            user        --- current poc user name
    output: <data_dir>/updates/<obsid>.<rev#>
            <data_dir>/updates_table.db
            <data_dir>/approved (if asis == 'asis'/'remove')
            various eamil sent out
            ch_line     --- a text listing parameters with updated values
            note        --- a notes to mp and arcops
    """
#
#--- set <obsid>.<rev#>
#
    obsidrev = set_obsidrev(ct_dict)
#
#--- check which parameter data are updated and create status data lists
#
    data     = get_conditions(ct_dict, ind_dict, asis)
#
#--- create data record file: <ocat_dir>/updates/<obsid>.<rev#>
#
    e_text, ch_line   = create_data_record_file(ct_dict, ind_dict, user, asis, data, obsidrev)
    
#
#--- only when the observation is still 'scheduled', 'unobserved'
#--- update database files and create notifications
#
    if  ct_dict['status'][-1]  in ['scheduled', 'unobserved', 'untriggered']:
        if asis in ['norm', 'asis']:
            send_param_change_notification(ct_dict, obsidrev, e_text, asis, data)

        elif asis in ['remove', 'clone']:
            send_clone_remove_notification(ct_dict, obsidrev, asis)
#
#--- update signoff status data in <ocat_dir>/updates_table.db
#
        update_status_data_file(ct_dict, user, asis, data[1], obsidrev)
#
#--- update approved list
#
        if asis in ['asis', 'remove']:
            update_approved_list(ct_dict, user, asis)
#
#--- check potential notification
#
        note = {}
        note1 = check_coordinate_shift(ct_dict)
        if note1 != []:
            note['coordinate_shift'] = note1
        note2 = check_obs_time(ct_dict)
        if note2 != []:
            note['obsdate_under10'] = note2
        note3 = check_or_list(ct_dict)
        if note3 != []:
            note['on_or_list'] = note3
        note4 = check_targname_change(ct_dict)
        if note4 != []:
            note['targname_change'] = note4
    else:
        ch_line = ''
        note    = {}

    return ch_line, note

#-----------------------------------------------------------------------------------------------
#-- get_conditions: extract parameters with updated values                                    --
#-----------------------------------------------------------------------------------------------

def get_conditions(ct_dict, ind_dict, asis):
    """
    extract parameters with updated values
    input:  ct_dict     --- a dict <param> <---> <imformation>
            ind_dict    --- a dict of <param> <---> 0: value is updated/ 1: value is same as before
            asis        --- asis status
    output: data1       --- a list of parameter names of different groups
            data2       --- a list of parameter names with updated values in different groups
    """
#
#--- save parameters of each group in a list
#
    gen_group  = []
    dt_group   = []
    tc_group   = ['time_ordr','window_constraint', 'tstart', 'tstop']
    rc_group   = []
    oc_group   = []
    hrc_group  = []
    acis_group = []
    awin_group = []
    rmks_group = []
#
#--- save parameters with values updated
#
    gen_list   = []
    acis_list  = []
    time_list  = []
    roll_list  = []
    awin_list  = []

    for param in ind_dict:
        chk   = ind_dict[param]         #--- if 0: the vaule updated/1: same
        group = ct_dict[param][3]
#
#--- sorting parameters into each group
#
        if group == 'gen':
            gen_group.append(param)
        elif group == 'dt':
            dt_group.append(param)
        elif group == 'rc':
            rc_group. append(param)
        elif group == 'oc':
            oc_group.append(param)
        elif group == 'hrc':
            hrc_group.append(param)
        elif group == 'acis':
            acis_group.append(param)
        elif group == 'awin':
            awin_group.append(param)
        elif group == 'remarks':
            rmks_group.append(param)
#
#--- for time constraint cases, only thoese parameters in pre-determined tc_group is checked
#
        if group == 'tc':
            if not param in tc_group:
                continue
#
#--- if asis status is "norm", checking any of the parameter values updated
# 
        if asis == 'norm':
            if group in ['rc', 'awin']:
                if isinstance(chk, list):
                    for k in range(0, 10):
                        if chk[k] == 1:
                            continue
                        keep = [param, k]
                        if group == 'rc':
                            roll_list.append(keep)
                        elif group == 'awin':
                            awin_list.append(keep)
                else:
                    if chk == 1:
                        continue
                    if group == 'rc':
                        roll_list.append(param)
                    else:
                        awin_list.append(param)
    
            elif param in tc_group:
                if isinstance(chk, list):
                    for k in range(0, 10):
                        if chk[k] == 1:
                            continue
                        keep = [param, k]
                        time_list.append(keep)
                else:
                    if chk == 0:
                        time_list.append(param)
            else:
                if chk == 1:
                    continue
                if group == 'acis':
                    acis_list.append(param)
                else:
                    gen_list.append(param)
#
#--- returning the results in two groups
#
    out1 = [gen_group, dt_group, tc_group, rc_group, oc_group,\
            hrc_group, acis_group, awin_group, rmks_group]
#
#--- don't compare acis window 'order' parm
#
    if 'ordr' in awin_list:
        awin_list.remove('ordr')

    out2 = [gen_list, acis_list, time_list, roll_list, awin_list]
    return [out1, out2]

#-----------------------------------------------------------------------------------------------
#-- create_data_record_file: create a data record file: <ocat_dir>/updates/<obsid>.<rev#>    ---
#-----------------------------------------------------------------------------------------------

def create_data_record_file(ct_dict, ind_dict, user, asis, data, obsidrev):
    """
    create a data record file: <ocat_dir>/updates/<obsid>.<rev#> 
    input:  ct_dict --- a dict <param> <---> <imformation>
            ind_dict    --- a dict of <param> <---> 0: value is updated/ 1: value is same as before
            user        --- poc name
            asis        --- asis status
            data        --- a list of lists of data [[a list of parameter list],[a list of updated param]]
            obsidrev    --- <obsid>.<rev#>
    output: <ocat_dir>/updates/<obsid>.<rev>
            line        --- content for email 
            cline       --- changed parameters
    """
#
#-- open up the passed data
#-- lists of parameter names in each group
#-- lists of parameter names with changed values in each group
#
    [gen_group, dt_group, tc_group, rc_group, oc_group,\
     hrc_group, acis_group, awin_group, rmks_group]  = data[0]

    [gen_list, acis_list, time_list, roll_list, awin_list] = data[1]
    line = ''
    cline = ''
#
#--- general information about this observation
#
    line = line + 'OBSID       = ' + str(ct_dict['obsid'][-1])   + '\n'
    line = line + 'SEQNUM      = ' + str(ct_dict['seq_nbr'][-1]) + '\n'
    line = line + 'TARGET      = ' + ct_dict['targname'][-1]     + '\n'
    line = line + 'USER NAME   = ' + user                        + '\n'
#
#--- submitting status
#
    if asis == 'asis':
        line = line + 'VERIFIED OK AS IS\n'
    elif asis == 'remove':
        line = line + 'VERIFIED AS REMOVED\n'
    elif asis == 'clone':
        line = line + 'VERIFIED AS CLONE\n'
    else:
        line = line + 'VERIFIED AS NORM\n'
#
#--- comment and remarks
#
    line = line + 'PAST COMMENTS = \n'
    line = line + ct_dict['comments'][-2] + '\n\n'

    if ind_dict['comments'] == 0:
        line = line + 'NEW COMMENTS  = \n'
        line = line + ct_dict['comments'][-1] + '\n\n'

        cline = cline + 'NEW COMMENTS  = \n'
        cline = cline + ct_dict['comments'][-1] + '\n\n'


    line = line + 'PAST REMARKS  = \n'
    line = line + ct_dict['remarks'][-2] + '\n\n'

    if ind_dict['remarks'] == 0:
        line = line + 'NEW REMARKS   = \n'
        line = line + ct_dict['remarks'][-1] + '\n\n'

        cline = cline + 'NEW REMARKS   = \n'
        cline = cline + ct_dict['remarks'][-1] + '\n\n'
#
#--- list parameters that the values were updated
#
    line  = line + '\nGENERAL CHANGES: \n'
    for param in gen_list:
        if param in skip_list:
            continue
        tline = create_compare_line(param, ct_dict)
        line  = line  + tline
        cline = cline + tline

    for param in time_list:
        tline = create_compare_line(param, ct_dict, 'time_ordr')
        line  = line  + tline
        cline = cline + tline

    for param in roll_list:
        tline = create_compare_line(param, ct_dict, 'roll_ordr')
        line  = line  + tline
        cline = cline + tline
        
    line = line + '\nACIS CHANGES: \n'
    for param in acis_list:
        tline = create_compare_line(param, ct_dict)
        line  = line  + tline
        cline = cline + tline

    line = line + '\nACIS WINDOW CHANGES: \n'
    for param in awin_list:
        tline = create_compare_line(param, ct_dict, 'aciswin_no')
        line  = line  + tline
        cline = cline + tline
        
    line = line + '\n' + '-'* 90 + '\n'
    line = line + 'Below is a full listing of obscat parameter values at the time of submission,\n'
    line = line + 'as well as new values submitted from the form.  If there is no value in column 3\n,'
    line = line + 'then this is an unchangeable parameter on the form.\n'
    line = line + 'Note that new RA and Dec could be slightly off due to rounding errors in\n'
    line = line + 'double conversion steps.\n\n'
    line = line + 'PARAM NAME\t\t\tORIGINAL VALUE\t\t\tREQUESTED VALUE\n'
    line = line + '-'* 90 + '\n'

    border = '\n' + '-' * 60 + '\n'
#
#--- general parameter list
#
    for param in gen_group:
        if ct_dict[param][2] == 'n':
            if not  param in ['si_mode', 'ra', 'dec']:
                continue
        if param in ['dra', 'ddec']:
            continue
        line = line + create_foramted_line(param, ct_dict)
    line = line + border
#
#--- dither parameter list
#
    line = line + create_lines_for_none_rank_group(dt_group, ct_dict)                + border
#
#--- time constraint list
#
    line = line + create_lines_for_rank_entries('time_ordr', tc_group, ct_dict)      + border
#
#--- roll constraint list
#        
    line = line + create_lines_for_rank_entries('roll_ordr', rc_group, ct_dict)      + border
#
#--- other constraint list
#        
    line = line + create_lines_for_none_rank_group(oc_group, ct_dict)                + border
#
#--- hrc list
# 
    line = line + create_lines_for_none_rank_group(hrc_group, ct_dict)               + border
#
#--- acis list
# 
    line = line + create_lines_for_none_rank_group(acis_group, ct_dict)              + border
#
#--- acis window constraint list
#
    line   = line + create_lines_for_rank_entries('aciswin_no', awin_group, ct_dict) + border
#
#--- write out to <ocat_dir>/updates/<obsid>.<rev>
#
    if  ct_dict['status'][-1]  in ['scheduled', 'unobserved', 'untriggered']:

        ofile  = os.path.join(current_app.config['OCAT_DIR'], 'updates', obsidrev)
        #
        # --- If revision file write fail's remove ofile then raise error
        # --- This prevents empty revision files from being created
        #
        try:
            with open(ofile, 'w', encoding='utf-8') as fo:
                fo.write(line)
        except Exception as e:
            os.system(f"rm -f {ofile}")
            raise(e)

    return line, cline

#-----------------------------------------------------------------------------------------------
#-- update_status_data_file: status table update: <ocat_dir>/updates_table.db                ---
#-----------------------------------------------------------------------------------------------

def update_status_data_file(ct_dict, user, asis, data, obsidrev):
    """
    status table update: <ocat_dir>/updates_table.db
    input:  ct_dict     --- a dict of <param> <--> <information>
            user        --- poc user
            asis        --- asis status
            data        --- a list of lists of parameter names with updated values
            obsidrev    --- <obsid>.<rev#>
    output: updated: <ocat_dir>/updates_table.db
    """
#
#--- open the data into each list
#
    [gen_list, acis_list, time_list, roll_list, awin_list] = data
    gen_list = gen_list + time_list + roll_list
#
#--- for the case that we don't need to check updated parameter values
#
    signoff_date = 'NULL'
    if asis in ['asis', 'remove']:
        general = 'NULL'
        acis    = 'NULL'
        acis_si = 'NULL'
        hrc_si  = 'NULL'
        signoff =  user
        signoff_date = f'"{get_today_date()}"'

    elif asis == 'clone':
        general = 'NA'
        acis    = 'NULL'
        acis_si = 'NULL'
        hrc_si  = 'NULL'
        signoff = 'NA'
#
#--- general case which needs to check updated parameter cases
#
    else:
#
#---- general tag
#
        if len(gen_list) > 0:
            general = 'NA'
        else:
            general = 'NULL'
#
#--- acis tag
#    
        if len(acis_list) > 0 or len(awin_list) > 0:
            acis    = 'NA'
        else:
            acis    = 'NULL'
#
#--- acis/hrc si tags
#    
        if ct_dict['instrument'][-1] in ['HRC-I', 'HRC-S']:
            acis_si = 'NULL'
            hrc_si  = 'NULL'
    
            if ct_dict['hrc_si_mode'][-1] in ['', 'default', 'DEFAULT', 'NULL']:
                if ct_dict['hrc_si_mode'][-2] in ['', 'default', 'DEFAULT', 'NULL']:
                    hrc_si  = 'NULL'
                else:
                    hrc_si = 'NA'

            elif ct_dict['hrc_si_mode'][-2] in ['', 'default', 'DEFAULT', 'NULL']:
                if ct_dict['hrc_si_mode'][-1] in ['', 'default', 'DEFAULT', 'NULL']:
                    hrc_si  = 'NULL'
                else:
                    hrc_si = 'NA'
                    
            else:
                #for hparam in ['hrc_si_mode', 'hrc_timing_mode', 'hrc_zero_block']:
                for hparam in ['hrc_si_mode',]:
                    chk = csd.compare_values(ct_dict[hparam][-2], ct_dict[hparam][-1])
                    if chk == 0:
                        hrc_si = 'NA'
                        break
        else:
            acis_si = 'NULL'
            hrc_si  = 'NULL'
    
            if len(acis_list) > 0 or len(awin_list) > 0:
                acis_si = 'NA'

            else:
#
#--- coordinate change happens, acis si mode needs to be reviewed
#
                for aparam in ['ra', 'dec']:
                    chk = csd.compare_values(ct_dict[aparam][-2], ct_dict[aparam][-1])
                    if chk == 0:
                        acis_si = 'NA'
                        break

        signoff = 'NA'

    ufile  = os.path.join(current_app.config['OCAT_DIR'], 'updates_table.db')
    rev_file = os.path.join(current_app.config['OCAT_DIR'], 'updates', obsidrev)
    rev_time = int(os.stat(rev_file).st_mtime)
    add_statement = f'INSERT INTO revisions (obsidrev, general_signoff, acis_signoff, acis_si_mode_signoff, hrc_si_mode_signoff, usint_verification, usint_date, sequence, submitter, rev_time)'
    add_statement += f'VALUES ({obsidrev}, "{general}", "{acis}", "{acis_si}", "{hrc_si}", "{signoff}", {signoff_date},{ct_dict["seq_nbr"][-1]}, "{user}", {rev_time})'.replace('"NULL"','NULL')
    if current_app.config['CONFIGURATION_NAME'] == 'localhost':
        print(add_statement)
#
#--- SQL query to database
#
    try:
        with closing(sq.connect(ufile)) as conn: # auto-closes
            with conn: # auto-commits
                with closing(conn.cursor()) as cur: # auto-closes
                    cur.execute(add_statement)
        
    except sq.IntegrityError:
        current_app.logger.error(traceback.format_exc())
        flash(f"{ufile} Database Integrity Failure.")
        email.send_error_email()
    except sq.OperationalError:
        current_app.logger.error(traceback.format_exc())
        current_app.logger.info(f"SQL Statement: {add_statement}")
        flash(f"Something went wrong and couldn't update {ufile}.")
        email.send_error_email()

#-----------------------------------------------------------------------------------------------
#-- update_approved_list: update approved data list                                           --
#-----------------------------------------------------------------------------------------------

def update_approved_list(ct_dict, user, asis):
    """
    update approved data list
    input:  ct_dict --- a dict of <param> <--> <information>
            user    --- a poc user name
            asis    --- asis status
    output: <data_dir>/approved
    """
    ofile  = os.path.join(current_app.config['OCAT_DIR'], 'approved')
#
#--- asis case
#
    if asis == 'asis':
        obsid = str(ct_dict['obsid'][-1])
        line  = obsid + '\t' + str(ct_dict['seq_nbr'][-1]) + '\t' 
        line  = line + user + '\t' + get_today_date() + '\n'
        with open(ofile) as f:
            data = [line.strip() for line in f.readlines()]
        lchk  = 0
        for ent in data:
            atemp = re.split('\s+', ent)
            if atemp[0] == obsid:
                flash('This observation is already in approved list.')
                lchk = 1
                break
#
#--- if the file is locked, sleep  up to 10 secs
#
        if lchk == 0:
            chk = ocf.sleep_while_locked(ofile)
            if chk:
                lock   = threading.Lock()
                with lock:
                    cmd   = 'cp -f ' + ofile + ' ' + ofile + '~'
                    os.system(cmd)
                    with open(ofile, 'a', encoding='utf-8') as fo:
                        fo.write(line)
            else:
                flash('Something went wrong and cannot open "approved" file.')
#
#--- remove from cus_approved list
#
    elif asis == 'remove':
        obsid = str(ct_dict['obsid'][-1])
        if ocf.is_file_locked(ofile):
            time.sleep(2)
        
        data   = ocf.read_data_file(ofile)

        chk  = ocf.sleep_while_locked(ofile)
        if chk:
            lock   = threading.Lock()
            with lock:
                cmd   = 'mv -f ' + ofile + ' ' + ofile + '~'
                os.system(cmd)
                line  = remove_data_line(data, obsid)
    
                with open(ofile, 'w', encoding='utf-8') as fo:
                    fo.write(line)
        else:
            flash('Something went wrong and cannot open "approved" file.')

#-----------------------------------------------------------------------------------------------
#-- remove_data_line: remove obsidrev line from a list of approve data                        --
#-----------------------------------------------------------------------------------------------

def remove_data_line(data, sobsid):
    """
    remove obsidrev line from a list of approve data
    input:  data    --- a list of approved data
            sobsid  --- <obsid>.<rev #> of the list to be removed
    output: line    --- a string of approved data to be printed
    """
    line = ''
    for ent in data:
        atemp = re.split('\s+', ent)
        if atemp[0] == sobsid:
            continue
        else:
            line = line + ent + '\n'
    return line

#-----------------------------------------------------------------------------------------------
#-- send_param_change_notification: send parameter change notification to poc                 --
#-----------------------------------------------------------------------------------------------

def send_param_change_notification(ct_dict, obsidrev, text, asis, data):
    """
    send parameter change notification to poc
    input:  ct_dict     --- dict of <parameter> <---> <informaiton>
            obsidirev   --- <obsid>.<rev #>
            text        --- a content to be sent out
            asis        --- status of the submission
    output: email to poc
    """
    sender    = 'cus@cfa.harvard.edu'
    recipient = current_user.email
    #Use edit type to determine BCC recievers
    bcc       = ''
    if len(data[1][0]) > 0 or len(data[1][1]) > 0:
        bcc = ARCOPS
#
#--- notification of Ocat Data Result to POC
#
    subject = 'Parameter Change Log: ' + obsidrev 
    if asis == 'asis':
        subject = subject + ' (Approved)'
        recipient = current_user.email
        bcc = ''

    email.send_email(subject, sender, recipient, text, bcc = bcc)

#-----------------------------------------------------------------------------------------------
#-- send_clone_remove_notification: send remove or clone request notification                ---
#-----------------------------------------------------------------------------------------------

def send_clone_remove_notification(ct_dict, obsidrev, asis):
    """
    send remove or clone request notification
    input:  ct_dict     --- dict of <parameter> <---> <informaiton>
            obsidirev   --- <obsid>.<rev #>
            asis        --- status of the submission
    output: email to poc
    """
    sender    = 'cus@cfa.harvard.edu'
    recipient = current_user.email
    obsid     = str(ct_dict['obsid'][-1])
#
#--- notification of Ocat Data Result to POC
#
    subject = 'Parameter Change Log: ' + obsidrev 
    if asis == 'clone':
        subject = subject + ' (Split Request)'
        text    = 'The request of splliting obsid: ' + obsid + ' was submitted.\n\n'
        text    = text + 'The reason of the split request is: \n'
        text    = text + ct_dict['comments'][-1] + '\n'

    elif asis == 'remove':
        subject = subject + ' (Remove Request)'
        text    = obsid + ' was removed from cus_approved list on your request.\n'
    email.send_email(subject, sender, recipient, text)

#-----------------------------------------------------------------------------------------------
#-- create_compare_line: create a line to display changed parameter value                     --
#-----------------------------------------------------------------------------------------------

def create_compare_line(data, ct_dict, r_param=''):
    """
    create a line to display changed parameter value
    input:  data    --- either parameter name or [parameter, rank]
            ct_dict --- a dict of <parameter> <---> <information>
    output: line    --- a display line
    """
    if isinstance(data, list):
        [param, k] = data
        line = param.upper() + str(k+1) + ' changed from ' + str(ct_dict[param][-2][k])
        line = line + ' to ' + str(ct_dict[param][-1][k]) + '\n'

    else:
        line = data.upper()             + ' changed from ' + str(ct_dict[data][-2])
        line = line + ' to ' + str(ct_dict[data][-1]) + '\n'
        
    return line

#-----------------------------------------------------------------------------------------------
#-- create_lines_for_none_rank_group:create a line to display parameter name and the original and new values
#-----------------------------------------------------------------------------------------------

def create_lines_for_none_rank_group(group, ct_dict):
    """
    create a line to display parameter name and the original and new values
    input:  group   --- a list of parameters
            ct_dict --- a dict of <param> <---> <information>
    output: line    --- a display line
    """
    line = ''
    for param in group:
        if ct_dict[param][2] == 'n':
            continue
        line = line + create_foramted_line(param, ct_dict)

    return line

#-----------------------------------------------------------------------------------------------
#-- create_lines_for_rank_entries: create a line to display parameter name etc for ranked entiries
#-----------------------------------------------------------------------------------------------

def create_lines_for_rank_entries(oparam, group, ct_dict):
    """
    create a line to display parameter name etc for ranked entiries
    input:  oparam  --- a parameter to indicate rank
            group   --- a list of parameters
            ct_dict --- a dict of <param> <---> <information>
    output: line    --- a display line
    """
    line   = create_foramted_line(oparam, ct_dict)
    rank   = ct_dict[oparam][-1]
    if ct_dict[oparam][-1] < ct_dict[oparam][-2]:
        rank   = ct_dict[oparam][-2]
    for k in range(0, rank):
        for param in group:
            if param == oparam:
                continue
            if isinstance(ct_dict[param][-1], list):
                line = line + create_foramted_line(param, ct_dict, k)

    return line

#-----------------------------------------------------------------------------------------------
#-- create_foramted_line: create a line with a format                                         --
#-----------------------------------------------------------------------------------------------

def create_foramted_line(param, ct_dict, k=''):
    """
    create a line with a format
    input:  param   --- a parameter name
            ct_dict --- a dict of <param> <--> <information>
            k       --- if integer, rank, otherwise ignored
    output: line    --- a display line
    """
    if k == '':
        name = param.upper()
        org  = str(ct_dict[param][-2])
        new  = str(ct_dict[param][-1])
    else:
        name = param + str(k+1)
        name = name.upper()
        org  = str(ct_dict[param][-2][k])
        new  = str(ct_dict[param][-1][k])

    line = "%-26s %-26s %-26s\n"  % (name, org, new)

    return line

#-----------------------------------------------------------------------------------------------
#-- get_today_date: get today's date in <mm>/<dd>/<yy> format                                ---
#-----------------------------------------------------------------------------------------------

def get_today_date():
    """
    get today's date in <mm>/<dd>/<yy> format
    input:   none
    output: <mm>/<dd>/<yy>
    """
    date  = time.strftime('%m/%d/%y', time.gmtime())

    return date

#-----------------------------------------------------------------------------------------------
#-- set_obsidrev: find the last revision # and set a new revision #                           --
#-----------------------------------------------------------------------------------------------

def set_obsidrev(ct_dict):
    """
    find the last revision # and set a new revision #
    input:  ct_dict     --- a dict of <param> <---> <information>
    output: obsidrev    --- <obsid>.<rev#> with the latest revision #
    """
    obsid = ct_dict['obsid'][-1]
    data = [each for each in os.listdir(f"{current_app.config['OCAT_DIR']}/updates/") if each.startswith(str(obsid)+".")]
    data.sort()
    if len(data) > 0:
        atemp = re.split('\.', data[-1])
        rev   = int(atemp[1]) + 1
    else:
        rev   = 1

    obsidrev = str(obsid) + '.' + ocf.add_leading_zero(rev, 3)
    return obsidrev

#-----------------------------------------------------------------------------------------------
#-- check_coordinate_shift: check whether there is a large coordindate shift                   --
#-----------------------------------------------------------------------------------------------

def check_coordinate_shift(ct_dict):
    """
    check whether there is a large coordindate shift
    input:  ct_dict --- a dict of <param> <--> <information>
    output: either <blank> or <obsid>
    """
    ora  = float(ct_dict['ra'][-1])
    nra  = float(ct_dict['ra'][-2])

    odec = float(ct_dict['dec'][-1])
    ndec = float(ct_dict['dec'][-2])

    diff = math.sqrt((ora - nra)**2 + (odec - ndec)**2)

    if diff > 0.1333:
        return [ct_dict['obsid'][-1],]
    else:
        return []

#-----------------------------------------------------------------------------------------------
#-- check_obs_time: check whether the observation is scheduled in less than 10 days           --
#-----------------------------------------------------------------------------------------------

def check_obs_time(ct_dict):
    """
    check whether the observation is scheduled in less than 10 days
    input:  ct_dict --- a dict of <param> <--> <information>
    output: either <blank> or <obsid>
    """
#
#--- check soe date is already assigned
#
    obs_time = ct_dict['soe_st_sched_date'][-1]
    if obs_time in null_list:
#
#--- if not, use lts date
#
        obs_time = ct_dict['lts_lt_plan'][-1]
        if obs_time in null_list:
            return []
#
#--- obs_time is in e.g., 'Aug 16 2021, 00:00AM' format
#
    atemp = re.split('\,', obs_time)
    btemp = re.split('\s+', atemp[0])
    mon   = ocf.change_month_format(btemp[0])
    mon   = ocf.add_leading_zero(mon, 2)
    day   = ocf.add_leading_zero(btemp[1], 2)
    year  = btemp[2]
    line  = year + '-' + mon + '-' + day

    ltime     = time.strftime('%Y:%j:%H:%M:%S', time.strptime(line, '%Y-%m-%d'))
    stime     = Chandra.Time.DateTime(ltime).secs
    time_diff = stime - now
    inday     = int(time_diff / 86400)

    if inday < 10:
        return [ct_dict['obsid'][-1],]
    else:
        return []

#-----------------------------------------------------------------------------------------------
#-- check_or_list: check whether the observation is on OR list                                --
#-----------------------------------------------------------------------------------------------

def check_or_list(ct_dict):
    """
    check whether the observation is on OR list
    input:  ct_dict --- a dict of <param> <--> <information>
    output: either <blank> or <obsid>
    """
    obsid   = str(ct_dict['obsid'][-1])
    or_list = os.path.join(current_app.config['OBS_SS'], 'scheduled_obs_list')
    data    = ocf.read_data_file(or_list)
    for ent in data:
        atemp = re.split('\s+', ent)
        if obsid == atemp[0]:
            return [ct_dict['obsid'][-1],]

    return  []

#----------------------------------------------------------------------------------------------
#-- check_targname_change: check whether there is a target name change                       --
#----------------------------------------------------------------------------------------------

def check_targname_change(ct_dict):
    """
    check whether there is a target name change
    input:  ct_dict --- a dict of <param> <--> <information>
    output: either <blank> or <obsid>
    """
    old = " ".join(ct_dict['targname'][-2].strip().split())
    new = " ".join(ct_dict['targname'][-1].strip().split())
    if old  != new:
        return [ct_dict['obsid'][-1],]
    else:
        return []

#-----------------------------------------------------------------------------------------------
