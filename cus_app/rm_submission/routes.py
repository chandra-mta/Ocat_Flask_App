#################################################################################
#                                                                               #
#       remove accidental submission                                            #
#                                                                               #
#       author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                               #
#       last update: Oct 28, 2021                                               #
#                                                                               #
#################################################################################
import os
import sys
import re
import string
import Chandra.Time
import time
import sqlite3 as sq
from contextlib import closing
import traceback
from datetime       import datetime

from flask          import render_template, flash, redirect, url_for, session
from flask          import request, g, jsonify, current_app
from flask_login    import current_user

from cus_app            import db
from cus_app.models     import User, register_user 
from cus_app.rm_submission    import bp
import cus_app.emailing as email

import cus_app.supple.ocat_common_functions         as ocf
#
#--- Define Globals
#
TODAY = datetime.now()
TODAY_STRING = TODAY.strftime('%m/%d/%y')
FETCH_SIZE = 1000

#----------------------------------------------------------------------------------
#-- before_request: this will be run before every time index is called          ---
#----------------------------------------------------------------------------------

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        session['session_start'] = int(Chandra.Time.DateTime().secs)
        session.permanent        = True
        session.modified         = True
    else:
        register_user()

#----------------------------------------------------------------------------------
#-- index: this is the main function to dispaly remove submission page           --
#----------------------------------------------------------------------------------

@bp.route('/',      methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    current_app.logger.info(f"Opening Remove Submission")
#
#--- data:      a list form of updates_table.db
#--- s_dict:    a dict of <obsid.rev> <--> <data info> for a given user
#--- disp_list: a list of last 10 entries on updates_table.db
#---            this one is used only when there is no entry that the user can 
#---            reverse the sign-off status
#--- mtime:     a file modified time; this will be used to check whether other updated the file
#--- warning    if True, someone updated the database file and display the warning
#
    fetch_result, s_dict = find_sign_off_entries()
    updates_file = os.path.join(current_app.config['OCAT_DIR'], 'updates_table.db')
    mtime        = ocf.find_file_modification_time(updates_file)
    warning      = False

    if 'submit_test' in request.form.keys():
#
#--- check whether the database file is modified while checking the data
#--- if not, update updates_table.db and possibly approved file
#
        ctime    = int(float(request.form['mtime']))
        if ctime > mtime:
            warning = True
        else:
            warning      = update_data_tables(request.form, fetch_result)
            fetch_result, s_dict = find_sign_off_entries()

        if warning == False:
            return redirect(url_for('rm_submission.index'))
    return render_template('rm_submission/index.html',
                            s_dict    = s_dict,
                            disp_list = [[format_display(entry), 10] for entry in fetch_result],
                            mtime     = mtime,
                            warning   = warning
                          )

#----------------------------------------------------------------------------------
#-- find_sign_off_entries: find entries which the user can reverse the sign-off status
#----------------------------------------------------------------------------------

def find_sign_off_entries():
    """
    find entries which the user can reverse the sign-off status
    input:  none, but read from <ocat_dir>/updates_table.db
    output: data    --- updates_table.db in a list format
            s_dict  --- a dict <obsidrev> <---> <data info
                        only entries which the user can reverse the sign-off status
                        are included
    """
    user  = current_user.username
    ufile = os.path.join(current_app.config['OCAT_DIR'], 'updates_table.db')
#
#--- SQL query to database
#
    with closing(sq.connect(ufile)) as conn: # auto-closes
        with conn: # auto-commits
            with closing(conn.cursor()) as cur: # auto-closes
                fetch_result = cur.execute(f"SELECT * from revisions ORDER BY rev_time DESC LIMIT {FETCH_SIZE}").fetchall()
#
#--- columns listed in the following order in the database:
#--- obsidrev (0), general_signoff (1), general_date (2), acis_signoff (3), acis_date (4)
#--- acis_si_mode_signoff (5), acis_si_mode_date (6), hrc_si_mode_signoff (7), hrc_si_mode_date (8)
#--- usint_verification (9), usint_date (10), sequence (11), submitter (12), rev_time (13) (creation of rev in epoch time)
#
    s_dict = {}
    for entry in fetch_result:
        if entry[9] == 'NA':
#
#--- Reverting regular signoffs
#
            for idx in range(7,0,-2): # Range between sign off column indexes in reverse order
                if entry[idx] == current_user.username:
                    if (TODAY - datetime.strptime(entry[idx+1],'%m/%d/%y')).days < 2:
#
#--- If the  current user signed off on this particular column within the last two days, then list it as reversible
#
                        s_dict[str(entry[0])] = [format_display(entry), (idx // 2) + 1]
                        break
                    else:
                        continue
        elif entry[9] == current_user.username:
#
#--- Obsid has been verified by the user. Therefore need to check if undoing 'asis' approval or a regular usint verification
#
            if (TODAY - datetime.strptime(entry[10],'%m/%d/%y')).days < 2:
#
#--- Check if it's an ASIS revision but noting if the sign columns are all None
#
                if (entry[1] == None) and (entry[3] == None) and (entry[5] == None) and (entry[7] == None):
                    s_dict[str(entry[0])] = [format_display(entry), 6]
                else:
                    s_dict[str(entry[0])] = [format_display(entry), 5]
            else:
                continue
    return fetch_result[:10], s_dict

#----------------------------------------------------------------------------------
#--  format_display: modify updates_table.db entries into Jinja2 parseable lists  -
#----------------------------------------------------------------------------------
def format_display(entry):
    """
    modify updates_table.db entries into Jinja2 parseable lists 
    input: entry -- SQLite updates_table.db data row entry
    output: data_list -- formatted list
    """
#
#--- columns listed in the following order in the database:
#--- obsidrev (0), general_signoff (1), general_date (2), acis_signoff (3), acis_date (4)
#--- acis_si_mode_signoff (5), acis_si_mode_date (6), hrc_si_mode_signoff (7), hrc_si_mode_date (8)
#--- usint_verification (9), usint_date (10), sequence (11), submitter (12), rev_time (13) (creation of rev in epoch time)
#
    data_list = [str(entry[0])]
#
#--- General Signoff
#
    if entry[1] in ['NA', 'N/A']:
        data_list.append(entry[1])
    elif entry[1] == None:
        data_list.append('NULL')
    else:
        data_list.append(f'{entry[1]} {entry[2]}')
#
#--- ACIS Signoff
#
    if entry[1] in ['NA', 'N/A']:
        data_list.append(entry[3])
    elif entry[1] == None:
        data_list.append('NULL')
    else:
        data_list.append(f'{entry[3]} {entry[4]}')
#
#--- ACIS SI Mode Signoff
#
    if entry[1] in ['NA', 'N/A']:
        data_list.append(entry[5])
    elif entry[1] == None:
        data_list.append('NULL')
    else:
        data_list.append(f'{entry[5]} {entry[6]}')
#
#--- HRC SI Mode Signoff
#
    if entry[1] in ['NA', 'N/A']:
        data_list.append(entry[7])
    elif entry[1] == None:
        data_list.append('NULL')
    else:
        data_list.append(f'{entry[7]} {entry[8]}')
#
#--- Usint Verification
#
    if entry[1] in ['NA', 'N/A']:
        data_list.append(entry[9])
    elif entry[1] == None:
        data_list.append('NULL')
    else:
        data_list.append(f'{entry[9]} {entry[10]}')

    data_list += [entry[11], entry[12]]
    return data_list

#----------------------------------------------------------------------------------
#--  update_data_tables: modify updates_table.db and possibly approved list     -
#----------------------------------------------------------------------------------

def update_data_tables(form):
    """
    modify updates_table.db and possibly approved list
    input;  form    --- form data
            data    --- a list format of updates_table.db
    output: updated <ocat_dir>/updates_table.db
                    <ocat_dir/approved
    """
    ufile = os.path.join(current_app.config['OCAT_DIR'], 'updates_table.db')
    approve_file = os.path.join(current_app.config['OCAT_DIR'],'approved')
#
#--- find out which entry is asked to be reversed sign-off status
#---        pos:0 --- this submission before any signing off
#---        pos:1 --- general
#---        pos:2 --- acis 
#---        pos:3 --- acis si mode
#---        pos:4 --- hrc si mode
#---        pos:5 --- verified by
#---        pos:6 --- verified by with approved entry
#
    for key in form.keys():
        if form[key] == 'Remove':
            atemp    = key.split("_")
            obsidrev = atemp[0]
            pos      = int(atemp[1])
#
#--- Parse options of pos for type of reversal action
#
            reversal_statement = None
            if pos == 0:
                file_remove = os.path.join(current_app.config['OCAT_DIR'],'updates',obsidrev)
                try:
                    os.system(f"rm -rf {file_remove}")
                except:
                    current_app.logger.error(f"Couldn't remove {file_remove} in rm_sumbission page.")
                    email.send_error_email()
                reversal_statement = f"DELETE FROM revisions WHERE obsidrev = {obsidrev}"
            elif pos == 1:
                reversal_statement = f"UPDATE revisions SET general_signoff = 'NA', general_date = NULL WHERE obsidrev = {obsidrev}"
            elif pos == 2:
                reversal_statement = f"UPDATE revisions SET acis_signoff = 'NA', acis_date = NULL WHERE obsidrev = {obsidrev}"
            elif pos == 3:
                reversal_statement = f"UPDATE revisions SET acis_si_mode_signoff = 'NA', acis_si_mode_date = NULL WHERE obsidrev = {obsidrev}"
            elif pos == 4:
                reversal_statement = f"UPDATE revisions SET hrc_si_mode_signoff = 'NA', hrc_si_mode_date = NULL WHERE obsidrev = {obsidrev}"
            elif pos == 5:
                reversal_statement = f"UPDATE revisions SET usint_verification = 'NA', usint_date = NULL WHERE obsidrev = {obsidrev}"
            elif pos == 6:
                reversal_statement = f"UPDATE revisions SET usint_verification = 'NA', usint_date = NULL WHERE obsidrev = {obsidrev}"
                with open(approve_file,'r') as f:
                    data = [line.strip() for line in f.readlines()]
                    line = write_approved_file(data, obsidrev)
                    with open(approve_file, 'w') as fo:
                        fo.write(line)
            if reversal_statement:
#
#--- SQL query to database
#
                with closing(sq.connect(ufile)) as conn: # auto-closes
                    with conn: # auto-commits
                        with closing(conn.cursor()) as cur: # auto-closes
                            cur.execute(reversal_statement)
                return False
            else:
                current_app.logger.error(f"Attempting to remove submission with undetermined status: {atemp}")
                email.send_error_email()
                return True
                
#----------------------------------------------------------------------------------
#-- write_approved_file: create obsidrev removed approved list for updating the datafile
#----------------------------------------------------------------------------------

def write_approved_file(data, obsidrev):
    """
    create obsidrev removed approved list for updating the datafile
    input:  data        --- a list of data
            obsidreve   --- <obsid>.<rev#>
    output: line        --- string of data to print out
    """
    approve_file = os.path.join(current_app.config['OCAT_DIR'],'approved')
    atemp = re.split('\.', obsidrev)
    obsid = atemp[0]
    line  = ''
    chk   = 0
    for ent in data:
        mc = re.search(obsid, ent)
        if mc is None:
            line = line + ent +  '\n'
        else:
            chk = 1
#
#--- the entry is in approved list; so update it with the list without the entry
#
    if chk == 1:
        if float(os.path.getsize(approve_file)) > 0:
            cmd = 'cp -f ' + approve_file + ' ' + approve_file + '~'
            os.system(cmd)

        send_notification(obsid)

    return line
        
#----------------------------------------------------------------------------------
#-- send_notification: sending removal from cus_approved list                    --
#----------------------------------------------------------------------------------

def send_notification(obsid):
    """
    sending removal from cus_approved list
    input:  obsid   --- obsid
    output: email sent out
    """
    sender    = 'cus@cfa.harvard.edu'
    recipient = current_user.email
    subject   = str(obsid) + ' is removed from cus_approved list'

    text      = 'Remove Accidental Submission Page removed ' + str(obsid) 
    text      = text + ' from cus_approved list.\n'

    email.send_email(subject, sender, recipient, text)