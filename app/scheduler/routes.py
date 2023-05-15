#########################################################################################
#                                                                                       #
#       scheduler page: display schedule sign-up page                                   #
#                                                                                       #
#           author: t.isobe (tisobe@cfa.harvard.edu)                                    #
#                                                                                       #
#           last update: Oct 25, 2021                                                   #
#                                                                                       #
#########################################################################################

import os
import sys
import re
import string
#import random
import time
import copy
import threading
import Chandra.Time

from flask              import render_template, flash, redirect, url_for, session
from flask              import request, current_app
from flask_login        import current_user, login_required

from app.scheduler      import bp
from app.emailing       import send_email
from app.models         import register_user

import app.supple.ocat_common_functions     as ocf  #--- save commonly used functions
import app.scheduler.read_poc_schedule      as rps  #--- create a data table from the database
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
#
#--- temporary file location/name
#
#rtail  = int(time.time() * random.random())
#zspace = '/tmp/zspace' + str(rtail)
#
#--- set a list of years (from the last year to five year from the last year)
#
year_list = ocf.set_year_list(chk=1)
#
#--- set a warning text
#
warning = "It seems that someone updated the schedule just before you "
warning = warning + "submited your update. Please check the schedule below  "
warning = warning + "(automatically updated) and re-submit your update. "
warning = warning + "If you just reloaded the page, please ignore this message."

#-------------------------------------------------------------------
#-- before_request: this will be run before every time index is called  
#-------------------------------------------------------------------
                                                                    
@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        session['session_start'] = int(Chandra.Time.DateTime().secs)
        session.permanent        = True
        session.modified         = True
#
#--- remove old temp files
#
        #ocf.clean_tmp_files()
    else:
        register_user()

#-------------------------------------------------------------------
#-- index: this is the main function to display scheduler page    --
#-------------------------------------------------------------------

@bp.route('/',      methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
#@login_required
def index():
    """
    schedule data table content:
            <user full name>
            <starting time in seconds from 1998.1.1>
            <starting time in [mm, dd, yyy]>
            <stopping time in [mm, dd, yyy]>
            <who assigned the slot>
            <indicator>:    -1  ---- the row is closed for editing
                             0  ---- the row is filled but can be re-oppen
                             1  ---- the row is open
                             2  ---- the row is filled but a wrong time interval
                             3  ---- the row is open with non-standard time span
                             4  ---- same as 1, but without a delete button
                             5  ---- same as 2, but without a delete button
                             6  ---- same as 3, but without a delete button
            <id of the data>
    """
    if current_app.config['DEVELOPMENT']:
        info_dir = '/proj/web-cxc/cgi-gen/mta/Obscat/ocat/Info_save/too_contact_info/'
#
#--- set poc list: [<poc id>,<full name>,<email>]
#---     poc dict: <poc id> <--> [<poc id>,<full name>,<email>]
#
    poc_list = ocf.read_poc_list(current_user.username)
    poc_list = [['tbd','TBD','na']] + poc_list 
    poc_dict = make_poc_dict(poc_list)
#
#--- read schedule database and create a data table
#--- mtime is the the data file last modification time
#
    ifile    = info_dir + 'schedule'
    schedule = rps.create_schedule_data_table(ifile)
    cfile    = info_dir + 'schedule'
    mtime    = ocf.find_file_modification_time(cfile)
    lchk     = 1
#
#--- update request is submitted...
#
    if 'submit_test' in request.form.keys():
#
#--- check whether someone updated the schedule table while the user was checking the data table
#
        ptime = int(float(request.form['mtime']))
        if mtime > ptime:
            flash(warning)
#
#--- if no one updated the schedule database, update this user's request
#
        else:
            schedule, uchk = udpate_data_table(request.form, schedule, poc_dict)
            schedule, lchk = update_schedule_database(schedule, poc_dict, uchk)
            mtime          = ocf.find_file_modification_time(cfile)
#
#--- if lchk is -1, it indicates that the database file is locked (someone is writing on it).
#--- if lchk is  0, it indicates that there are time gaps among the poc duty period.
#--- if lchk is  1, it indicates everything is fine and the script will update the databse.
#
            if lchk < 0:
                flash(warning)
                schedule = rps.create_schedule_data_table()
                mtime    = ocf.find_file_modification_time(cfile)
                lchk     = 1
#
#--- create/update the html page
#
    return render_template('scheduler/index.html', \
                            data_list    = schedule,
                            poc_list     = poc_list, 
                            year_list    = year_list,
                            mtime        = mtime, 
                            lchk         = lchk)

#-------------------------------------------------------------------
#-- udpate_data_table: update schedule data table according to submitted data
#-------------------------------------------------------------------

def udpate_data_table(data, schedule, poc_dict):
    """
    update schedule data table according to submitted data
    input:  data        --- submitted data
            scheudle    --- a list of lists of schedule data
            posc_dict   --- a dictionary of <poc id> <---> <poc info>
    output: schedule    --- udpated schedule data table
            uchk        --- an indicator of what was clicked
                            if uchk < 0, it is Split/Delete button is clicked
                            and we don't want to send email out
    """
    slen  = len(schedule)
    uchk  = 0                   #--- indicator of what was clicked
    orows = []                  #--- keeps open row ids
    for cid in range(0, slen):
#
#--- check whether a unlock request on any of the filled rows
#
        name = 'unlock' + str(cid)
        if name in data.keys():
            val  = data[name]     
            if val == 'Unlock':
                schedule[cid][0]    = 'TBD'
                schedule[cid][-3]   = ''
                schedule[cid][-2]   = rps.check_time_interval(schedule, cid)
#
#--- also update the status of status of the neighboring rows
#
                if schedule[cid-1][0] == 'TBD':
                    schedule[cid-1][-2] = rps.check_time_interval(schedule, cid-1)

                if schedule[cid+1][0] == 'TBD':
                    schedule[cid+1][-2] = rps.check_time_interval(schedule, cid+1)
                uchk = 1

                return schedule, uchk
#
#--- check open rows
#
        else:
            orows.append(cid)
#
#--- check whether split/delete is requested on an open row
#
            for head in ['split', 'delete']:
                if get_data_from_form(data, head, cid)  ==  head.capitalize():
                    if head == 'split':
                        schedule = add_row(schedule, cid)
                    else:
                        schedule = delete_row(schedule, cid)
        
                    uchk = -1
                    return schedule, uchk
#
#--- check whether update is requested on the open rows
#
            if get_data_from_form(data, 'update', cid) == 'Update':
                uchk = 1
#
#--- if update is requested, check which rows are updated;
#--- there could be more than one updated rows.
#
    if uchk > 0:
        for cid in orows:
#
#--- if poc is assigned, we assume that the rows are updated
#
            if not get_data_from_form(data, 'poc', cid) in ['TBD', 'NA', '']:
                try:
                    schedule = update_schedule(data, schedule, cid, poc_dict)
                except:
                    pass
    
    return schedule, uchk

#-------------------------------------------------------------------
#-- add_row: split and add a new data row to the schedule        ---
#-------------------------------------------------------------------

def add_row(schedule, cid):
    """
    split and add a new data row to the schedule
    input:  schedule    --- a list of lists of schedule data
            cid         --- id/row number of the data to be splited
    output: schedule    --- updated schedule table data
    """
#
#--- data row to be splited into two parts
#
    data_row        = schedule[cid]
#
#--- current starting and ending times in Chandra Time
# 
    stime           = int(data_row[1])
    stop_mon        = data_row[3][0]
    stop_day        = data_row[3][1]
    stop_year       = data_row[3][2]
    etime           = rps.convert_time_format_chandra([stop_mon, stop_day, stop_year])
#
#--- check whether we have enough date span to split this row
#
    tdelta          = etime - stime
    if tdelta <= 172800.0:              #--- 2 days
        flash("Sorry there is not enough time to split the row you specified.")
        return schedule
#
#--- if there is enough days, take a mid point to split the data row
#
    mstime          = 0.5 * (stime + etime)
    mstime2         = mstime + 86400    #--- the second rows is starting from the next day
#
#--- make sure that the starting time of the second row is smaller than or equal to the closing time
#
    if mstime2 >= etime:
        mstime2 = etime

    mtime           = rps.convert_time_format_chandra(mstime)
    mtime2          = rps.convert_time_format_chandra(mstime2)

    data_row2       = copy.deepcopy(data_row)
#
#--- update the ending time of the original row
#
    data_row[3][0]  = mtime[0]
    data_row[3][1]  = mtime[1]
    data_row[3][2]  = mtime[2]
    data_row[-2]    = rps.check_time_interval(stime, mstime)

    schedule[cid]   = data_row
#
#--- crate a new row with starting time a day after the updated original row
#
    data_row2[1]    = mstime2
    data_row2[2][0] = mtime2[0]
    data_row2[2][1] = mtime2[1]
    data_row2[2][2] = mtime2[2]
    data_row2[-2]   = rps.check_time_interval(mstime2, etime)
#
#--- insert the data into the schedule
#
    schedule.insert(cid+1, data_row2)
#
#--- update row id/number; id is kept as a string
#
    for k in range(cid+1, len(schedule)):
        schedule[k][-1] = str(int(schedule[k][-1]) + 1)

    return schedule

#-------------------------------------------------------------------
#-- delete_row: remove a row specified by row id from schedule     -
#-------------------------------------------------------------------

def delete_row(schedule, cid):
    """
    remove a row specified by row id from schedule
    input:  schedule    --- a list of lists of schedule input
            cid         --- an id of the row to be removed
    output: schedule    --- updated schedule
    """
#
#--- checking whether there is a data one after of this row
#
    try:
        test  = schedule[cid+1][0]
        ctest = 1
    except:
        ctest = 0
#
#--- both rows, one before and one after, are open
#
    chk  = 0
    if (ctest > 0) and (schedule[cid-1][0] == 'TBD') and (schedule[cid+1][0] == 'TBD'):
#
#--- find period lengths of the both period
#
        diff1 = schedule[cid][1]   - schedule[cid-1][1]

        mon   = schedule[cid+1][3][0]
        day   = schedule[cid+1][3][1]
        year  = schedule[cid+1][3][2]
        ltime = year + ':' + ocf.add_leading_zero(mon) + ':' + ocf.add_leading_zero(day)
        ltime = time.strftime('%Y:%j:00:00:00', time.strptime(ltime, '%Y:%m:%d'))
        stime = int(Chandra.Time.DateTime(ltime).secs)
        diff2 = stime - schedule[cid+1][1]
#
#--- choose the period with a shorter period span 
#
        if diff2 <= diff1:
            chk = 1                 #--- select one after
        else:
            chk = 0                 #--- select one before
#
#--- the case one period before is open but not one after
#            
    elif schedule[cid-1][0] == 'TBD':
            chk = 0
#
#--- the case one period after is open but not one before
#
    elif (ctest > 0) and (schedule[cid+1][0] == 'TBD'):
            chk = 1
#
#--- both sides of rows are already filled; you cannot remove this row
#
    else:
        flash('Sorry, but you cannot remove the row you specified.')
        return schedule
#
#--- combine the period with the row one before
#
    if chk == 0:
        schedule[cid-1][3][0] = schedule[cid][3][0]     #--- month
        schedule[cid-1][3][1] = schedule[cid][3][1]     #--- day
        schedule[cid-1][3][2] = schedule[cid][3][2]     #--- year
        schedule[cid-1][-2]   = rps.check_time_interval(schedule, cid-1)
#
#--- combine the period with the row one after
#
    elif chk == 1:
        schedule[cid+1][1]    = schedule[cid][1]        #--- chandra time
        schedule[cid+1][2][0] = schedule[cid][2][0]     #--- month
        schedule[cid+1][2][1] = schedule[cid][2][1]     #--- day
        schedule[cid+1][2][2] = schedule[cid][2][2]     #--- year
        schedule[cid+1][-2]   = rps.check_time_interval(schedule, cid+1)
#
#---  removed the row...
#
    del schedule[cid]
#
#--- lower the row id by 1 for the remaining rows
#
    for k in range(cid, len(schedule)):
        schedule[k][-1] = str(int(schedule[k][-1]) -1)

    return schedule
        
#-------------------------------------------------------------------
#-- update_schedule: update schedule data row                    ---
#-------------------------------------------------------------------

def update_schedule(data, schedule, cid, poc_dict):
    """
    update schedule data row
    input:  data        --- data form
            schedule    --- a list of lists of schedule data
            cid         --- row id/number to be updated
            poc_dict    --- a dict of <poc_id> <---> <poc info>
    output: schedule    --- updated schedule data
    """
#
#--- poc in duty; if poc_id is 'tbd', don't modify the rest of the information
#
    poc_id              = get_data_from_form(data, 'poc',    cid)
    if poc_id == 'tbd':
        return schedule
#
#--- converting poc_id to a spelled out full name
#
    schedule[cid][0]    = poc_dict[poc_id][1]
#
#--- beginning of the duty period
#
    dmon                = get_data_from_form(data, 'monbgn', cid)
    dday                = get_data_from_form(data, 'daybgn', cid)
    dyear               = get_data_from_form(data, 'yrbgn',  cid)
    stime               = rps.convert_time_format_chandra([dmon, dday, dyear])

    schedule[cid][1]    = stime
    schedule[cid][2][0] = dmon 
    schedule[cid][2][1] = dday 
    schedule[cid][2][2] = dyear
#
#--- ending of the duty period
#
    schedule[cid][3][0] = get_data_from_form(data, 'monend', cid)
    schedule[cid][3][1] = get_data_from_form(data, 'dayend', cid)
    schedule[cid][3][2] = get_data_from_form(data, 'yrend',  cid)
#
#--- who sign in the poc
#
    if poc_id == 'tbd':
        schedule[cid][4] = ' '
    else:
        schedule[cid][4] = current_user.username
#
#--- indicates that the row data status is now 'filled'
#
    schedule[cid][5]    = 0
#
#--- also update the status of the neibhboring rows
#
    if schedule[cid-1][0] == 'TBD':
        schedule[cid-1][-2] = rps.check_time_interval(schedule, cid-1)

    if schedule[cid+1][0] == 'TBD':
        schedule[cid+1][-2] = rps.check_time_interval(schedule, cid+1)

    return schedule

#-------------------------------------------------------------------
#-- get_data_from_form: read data from the form                   --
#-------------------------------------------------------------------

def get_data_from_form(fdata, head, cid):
    """
    read data from the form
    input:  fdata   --- form data
            head    --- header part of the data name
            cid     --- row id/number of the data
    output: data    --- the data value
    """
    name = head + str(cid)
    try:
        data = fdata[name]
    except:
        data = 'NA'  

    return data

#-------------------------------------------------------------------
#-- make_poc_dict: make poc id <---> pos info dictonary           --
#-------------------------------------------------------------------

def make_poc_dict(poc_list):
    """
    make poc id <---> pos info dictonary
    input:  poc_list    --- a list of list 
    output: poc_dict    --- a dict of <poc id> <--> [<poc id>, <poc full name>,<poc email>]
    """
    poc_dict = {}
    for ent in poc_list:
        poc_dict[ent[0]] = ent

    return poc_dict

#-------------------------------------------------------------------
#-- update_schedule_database: update schedule database            --
#-------------------------------------------------------------------

def update_schedule_database(schedule, poc_dict, uchk):
    """
    update schedule database

    input:  schedule        --- a schedule data table
            poc_dict        --- a dict of <poc id> <---> [<poc id>, <poc full name>, <poc emai>]
            uchk            --- if uchk < 0, it is split/delete
    output: <d_dir>/schedule--- an updated schedule databse
            c_chk           --- if time spans are not set correctly it will return 
                                a list of row ids of the wrong time intervals
                                else return 1 
    """
    if current_app.config['DEVELOPMENT']:
        info_dir = '/proj/web-cxc/cgi-gen/mta/Obscat/ocat/Info_save/too_contact_info/'
#
#--- output file name
#
    ofile = info_dir + 'schedule'
#
#--- read the current schedule data from the database
#
    pschedule  = rps.create_schedule_data_table()
#
#--- check wether the schedule file is locked; it means that someone just updated the 
#--- schedule database. if that is the case, don't update the database
#
    if ocf.is_file_locked(ofile):
        c_chk = -1
#
#--- update the schedule database; lock the file before updating
#
    else:
        lock = threading.Lock()
        with lock:
            with open(ofile, 'w') as fo:
                line, c_chk = create_schedule_line(schedule, pschedule, ofile)
                fo.write(line)
#
#--- if this change is sign-up or re-opening of a poc duty period, send email to 
#--- the current user, and possibly other pocs about the changes
#
        if uchk >= 0:
            send_update_notification(schedule, pschedule, poc_dict)

    return schedule, c_chk

#-------------------------------------------------------------------
#-- create_schedule_line: create updated input data line for print -
#-------------------------------------------------------------------

def create_schedule_line(schedule, pschedule, ofile):
    """
    create updated input data line for print
    input:  schedule        --- a schedule data table
            pschedule       --- the current schedule data 
            ofile           --- output data file name
    output: line            --- updated input data line
            c_chk           --- if time spans are not set correctly it will return 
                                a list of row ids of the wrong time intervals
                                else return 1 
    """
#
#--- copy the current database to a backup postion
#
    cmd   = 'cp -f ' + ofile + ' ' + ofile + '~'
    os.system(cmd)
#
#--- check whether the interval are correctly set
#--- if it is not, either adjust the time spans of rows one before or after
#--- if c_chk == 0: there are time gaps/if 1, no gaps
#
    schedule, c_chk  = check_time_span(schedule, pschedule)

    line = ''
    for k in range(0, len(schedule)):
        ent  = schedule[k]
#
#--- if the time span of the row is not correct, use the previous schedule data
#
        if ent[-2] in [2, 5]:
            ent  = pschedule[k]

        line = line + ent[0]    + '\t'         #--- poc    
        line = line + ent[2][0] + '\t'         #--- starting month
        line = line + ent[2][1] + '\t'         #--- starting day
        line = line + ent[2][2] + '\t'         #--- starting year
        line = line + ent[3][0] + '\t'         #--- ending month
        line = line + ent[3][1] + '\t'         #--- ending day
        line = line + ent[3][2] + '\t'         #--- ending year
        line = line + ent[4]    + '\n'         #--- signed off by

    return line,  c_chk

#------------------------------------------------------------------
#-- send_update_notification: sending email to the user to notify the update of the schedule
#-------------------------------------------------------------------

def send_update_notification(schedule, pschedule, poc_dict):
    """
    sending email to the user and possible other POC to notify the update of the schedule
    input:  poc_dict    --- a dict of <pocid> <---> <poc info>
    output: email sent out to the current user and possible other POCs
    """
#
#--- current user's id and full name
#
    user    = current_user.username
    fname   = poc_dict[user][1]

    save1   = []                #--- saving  signed up data
    save2   = []                #--- saving  removed data
    d_dict1 = {}                #--- saving the data of POC other than the current user (save1)
    d_dict2 = {}                #--- saving the data of POC other than the current user (save2)
    for k in range(0, len(schedule)):
        p_ent = pschedule[k]
        n_ent = schedule[k]
#
#--- if the time span of the row is not correct, skip that row
#
        if n_ent[-2] in [2, 5]:
            continue
#
#--- if user names are same in both schedules, nothing changed.
#
        if p_ent[0] == n_ent[0]:
            continue
#
#--- something has changed; keep the record (<user name>, <starting time>,<stopping time>)
#
        else:
#
#--- a poc selected the row for the duty
#
            if p_ent[0] == 'TBD':
                data = [n_ent[0], n_ent[2], n_ent[3]]
                save1.append(data)
#
#--- checking whether the crrent user signed up this period for another poc
#
                if poc_dict[user][1] != n_ent[0]:
                    dpoc = check_poc_match(poc_dict, n_ent[0])
                    try:
                        out = d_dict1[dpoc]
                        out.append(data)
                    except:
                        out = [data]
                    d_dict1[dpoc] = out
#
#--- a poc duty is re-opened for the row
#
            elif n_ent[0] == 'TBD':
                data = [p_ent[0], p_ent[2], p_ent[3]]
                save2.append(data)
#
#--- checking whether the crrent user removed this period for another poc
#
                if poc_dict[user][1] != p_ent[0]:
                    dpoc = check_poc_match(poc_dict, p_ent[0])
                    try:
                        out = d_dict2[dpoc]
                        out.append(data)
                    except:
                        out = [data]
                    d_dict2[dpoc] = out
#
#--- create the content of email
#
    sender    = 'cus@cfa.harvard.edu'
    subject   = 'Update in POC Duty SignUp'
    bcc       = 'cus@cfa.harvard.edu'
#
#-- send out email to the current user
#
    line = ''
    if len(save1) > 0:
        line = line + 'You modified the POC duty on the following period(s):\n\n'
        line = write_email_lines(line, save1)

    if len(save2) > 0:
        line = line + '\nYou re-opened following period(s) for POC duty sign-up:\n\n'
        line = write_email_lines(line, save2)

    if line != '':
        line = line + 'If you signed up/removed for someone else, make sure to notify the POC.\n'
        poc_email = poc_dict[user][-1]
        send_email(subject, sender, poc_email, line, bcc)
#
#--- send email to other POCs if the current user assigned/changed the POC duty periods on them
#
    for poc_id in poc_dict.keys():
        try:
            out = d_dict1[poc_id]
        except:
            out = []

        try:
            out2 = d_dict2[poc_id]
        except:
            out2 = []

        line = ''
        if len(out) > 0:
            line = fname + ' updated your POC duty period(s):\n\n'
            line = write_email_lines(line, out)
    
        if len(out2) > 0:
            line = fname + ' removed following period(s) from  your POC duty period(s):\n\n'
            line = write_email_lines(line, out2)
    
        if line != '':
            line = line + '\n\nIf this is not expected, please contact ' + fname  + ' '
            line = line + '(' + poc_dict[user][-1] + ').'
    
            poc_email = poc_dict[poc_id][-1]

            send_email(subject, sender, poc_email, line, bcc)

#-------------------------------------------------------------------
#-- write_email_lines: create email signoff/removed entry table   --
#-------------------------------------------------------------------

def write_email_lines(line, cdata):
    """
    create email signoff/removed entry table
    input:  line    --- a line from the previous section
            cdata   --- a list of lists of date date
    output: line    --- an updated line
    """
    line = line + 'POC\t\tStarting\tEnding\n'
    line = line + '\t\t\tMon Day Year   Mon Day Yeear\n'
    for ent in cdata:
        line  = line + ent[0] + '\t'
        line  = line + ent[1][0] + '  ' + ent[1][1] + '  ' + ent[1][2] + '\t'
        line  = line + ent[2][0] + '  ' + ent[2][1] + '  ' + ent[2][2] + '\n\n'

    return line

#-------------------------------------------------------------------
#-- check_poc_match: find poc id from POC full name              ---
#-------------------------------------------------------------------

def check_poc_match(poc_dict, name):
    """
    find poc id from POC full name
    input:  poc_dict    --- a dict of poc_id <-->[poc_id, poc full name, poc email]
            name        --- poc full name
    output: poc         --- poc id
    """
    poc = 'tbd'
    for key in poc_dict.keys():
        if poc_dict[key][1] == name:
            poc = key
            break
    return poc
        
#-------------------------------------------------------------------
#-- check_time_span: check the gaps and/or the overlaps of the assigned time span
#-------------------------------------------------------------------

def check_time_span(schedule, pschedule):
    """
    check the gaps and/or the overlaps of the assigned time span
    input:  schedule    --- a list of lists of schedule data
            pschedule   --- a list of previous schedule data
    output: schedule    --- with adjusted time interval or wrong interval markers
                            indicator 2 --- a wrong interval and need to modify
                                      3 --- a time interval is not standard
            c_chk       --- 1 if no time span problem
                            0 there is a gap 
    """
    c_chk  = 1 
    for k in range(0, len(schedule) -1):
        if schedule[k][-2] < 0:
            continue
#
#--- if poc is not updated from the previous schedule, nothing was updated
#
        poc    = schedule[k][0]
        ppoc   = pschedule[k][0]        #--- poc of the previous schedule data
        if poc in [ppoc, 'TBD']:
            continue
#
#--- check whether row one before and one after are still open. if yes, 0, else 3
#
        add    = rps.update_status_ind(schedule, k)
#
#--- current starting and stopping time period
#
        btime  = rps.convert_time_format_chandra(schedule[k][2])
        etime  = rps.convert_time_format_chandra(schedule[k][3])
#
#--- check whether the ending time is smaller than the starting time
#
        if etime < btime:
            schedule[k][-2] = 2 + add
            c_chk           = 0
#
#--- check stopping time of the previous row is one day before this starting time
#--- note that there is +/- 10 mins of margin so that we don't need to worry about 
#--- a small variation (e.g., leap second or roundup)
#
        else:
            cpoc   = schedule[k-1][0]
            stime  = rps.convert_time_format_chandra(schedule[k-1][2])
            ctime  = rps.convert_time_format_chandra(schedule[k-1][3])
            ctime1 = ctime + 85600
            ctime2 = ctime + 87000
#
#-- if the row order is totally out, mark the row and don't update the span
#
            if etime < ctime:
                schedule[k][-2] = 2 + add
                c_chk           = 0
#
#--- check whether the time spans are in order. if not, adjust the time span(s)
#
            elif btime < ctime1 or btime > ctime2:
#
#--- if the row before is marked as a wrong time span, don't update the sapn  of this row
#
                if schedule[k-1][-2] in [2, 5]:
                    continue
#
#--- if the range has a gap and the poc of one row before is 'TBD', adjust 
#--- the stopping time of the previous row to fill the gap and mark as "adjusted" (3)
#
                if cpoc == 'TBD':
                    mtime  = btime - 86400
#
#--- make sure that the adjusted ending time is not smaller than the starting time
#
                    if mtime > stime:
                        ltime             = rps.convert_time_format_chandra(mtime)
                        schedule[k-1][1]  = mtime
                        schedule[k-1][3]  = ltime
                        schedule[k-1][-2] = 3 + rps.update_status_ind(schedule, k-1)
                    else:
                        schedule[k][-2]   = 2 + add
                        c_chk             = 0
#
#--- if the range has a gaps and the poc of one row before is not 'tbd', mark this row
#--- needs to be adjusted (2)
#
                else:
                    schedule[k][-2] = 2 + add
                    c_chk           = 0
#
#--- check a row after for the similar gap
#
            apoc   = schedule[k+1][0]
            atime  = rps.convert_time_format_chandra(schedule[k+1][2])
            stime  = rps.convert_time_format_chandra(schedule[k+1][3])
            atime1 = atime - 87000
            atime2 = atime - 85800

            if btime > atime:
                schedule[k][-2] = 2 + add
                c_chk           = 0

            elif etime < atime1 or etime > atime2:
                if schedule[k][-2] in [2, 5]:
                    continue

                if apoc == 'TBD':
                    mtime             = etime + 86400
                    if mtime < stime:
                        ltime             = rps.convert_time_format_chandra(mtime)
                        schedule[k+1][1]  = mtime
                        schedule[k+1][2]  = ltime
                        schedule[k+1][-2] = 3 + rps.update_status_ind(schedule, k+1)
                    else:
                        schedule[k][-2] = 2 + add
                        c_chk           = 0
                else:
                    schedule[k][-2] = 2 + add
                    c_chk           = 0

    return schedule, c_chk
            
