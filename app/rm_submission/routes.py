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
import random
import threading
from datetime       import datetime

from flask          import render_template, flash, redirect, url_for, session
from flask          import request, g, jsonify, current_app
from flask_login    import current_user, login_required

from app            import db
from app.models     import User, register_user 
from app.rm_submission    import bp
import app.email    as email

import app.supple.ocat_common_functions         as ocf
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
#--- temprary writing space
#
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)
#
#--- current chandra time and a day and a half ago
#
now   = int(Chandra.Time.DateTime().secs)
ytime = now - 86400 * 1.5
#
#---- set file names with a full path
#
updates_file = ocat_dir + 'updates_table.list'
approve_file = ocat_dir + 'approved'

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
#@login_required
def index():
#
#--- data:      a list form of updates_table.list
#--- s_dict:    a dict of <obsid.rev> <--> <data info> for a given user
#--- disp_list: a list of last 10 entries on updates_table.list
#---            this one is used only when there is no entry that the user can 
#---            reverse the sign-off status
#--- mtime:     a file modified time; this will be used to check whether other updated the file
#--- warning    if True, someone updated the database file and display the warning
#
    data, s_dict = find_sign_off_entries()
    disp_list    = create_display_data(data)
    mtime        = ocf.find_file_modification_time(updates_file)
    warning      = False

    if 'submit_test' in request.form.keys():
#
#--- check whether the database file is modified while checking the data
#--- if not, update updates_table.list and possibly approved file
#
        ctime    = int(float(request.form['mtime']))
        if ctime > mtime:
            warning = True
        else:
            warning      = update_data_tables(request.form, data)
            data, s_dict = find_sign_off_entries()
            disp_list    = create_display_data(data)

        if warning == False:
            return redirect(url_for('rm_submission.index'))

    return render_template('rm_submission/index.html',
                            s_dict    = s_dict,
                            disp_list = disp_list,
                            mtime     = mtime,
                            warning   = warning
                          )

#----------------------------------------------------------------------------------
#-- find_sign_off_entries: find entries which the user can reverse the sign-off status
#----------------------------------------------------------------------------------

def find_sign_off_entries():
    """
    find entries which the user can reverse the sign-off status
    input:  none, but read from <ocat_dir>/updates_table.list
    output: data    --- updates_table.list in a list format
            s_dict  --- a dict <obsidrev> <---> <data info
                        only entries which the user can reverse the sign-off status
                        are included
    """
    user  = current_user.username
#
#--- read data table and reverse the order so that we can check from newest
#
    data  = ocf.read_data_file(updates_file)
    data.reverse()
#
#--- check only the first 1000 or less
#
    dlen = len(data)
    if dlen > 1000:
        dlen = 1000
    s_dict = {}
    for k in range(0, dlen):
#
#--- find entries of the row signed off by the user
#
        mc = re.search(user, data[k])
        if mc is None:
            continue
#
#--- if the obsid is not verified by a POC
#--- check in order of acis/hrc si mode then general/acis. if si mode was signed off
#--- we don't need to check general/acis
#
        atemp = re.split('\t+', data[k])
        if atemp[5] == 'NA':                    #--- indicates that obsid.rev is not verified yet
            chk = 0
            for m in range(4, 0, -1):
#
#--- checking whether the entry is signed off by the user
#
                mc = re.search(user, atemp[m])
                if mc is not None:
                    btemp = re.split('\s+', atemp[m])
#
#--- if the signing off was more than a day and a half old, the user cannnot
#--- reverse the signoff
#
                    stime = convert_display_time_to_chandra(btemp[1])
                    if stime < ytime:
                        continue
                    else:
                        s_dict[atemp[0]] = [atemp, m]
                        chk = 1
                        break
                else:
#
#--- the entry is either not signed off or signed off by someone else
#--- if it is signed off by someone else, stop checking
#
                    if atemp[m] in ['NULL', 'NA']:
                        continue
                    else:
                        chk = 1
                        break
#
#--- the data is submitted the data from Ocat Data Page
#
            if chk == 0:
                s_dict[atemp[0]] = [atemp, 0]
#
#--- if the obsid is verified by the user
#
        else:
            mc = re.search(user, atemp[5])
            if mc is not None:
                btemp = re.split('\s+', atemp[5])
                stime = convert_display_time_to_chandra(btemp[1])
                if stime < ytime:
                    continue
                else:
#
#--- check whether this is "asis" submission. if so, position is 6 to
#--- indicate that. 
#
                    chk = 0
                    for k in range(0, 4):
                        if atemp[k+1] == 'N\A':
                            atemp[k+1] = 'NA'

                        if atemp[k+1] != 'NULL':
                            chk += 1

                    if chk > 0:
                        s_dict[atemp[0]] = [atemp, 5]
                    else:
                        s_dict[atemp[0]] = [atemp, 6]

    return data, s_dict

#----------------------------------------------------------------------------------
#--  update_data_tables: modifiy updates_table.list and possibley approved list   -
#----------------------------------------------------------------------------------

def update_data_tables(form, data):
    """
    modifiy updates_table.list and possibley approved list
    input;  form    --- form data
            data    --- a list format of udpates_table.list
    output: updated <ocat_dir>/updates_table.list
                    <ocat_dir/approved
    """
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
            atemp    = re.split('_', key)
            obsidrev = atemp[0]
            pos      = int(float(atemp[1]))
#
#--- go through each entry 
#
    chk = 0
    save = []
    for ent in data:
#
#--- if chk == 1, the modification is already done; so skip checking
#
        if chk == 0:
#
#--- the data row with the <obsid>.<rev> is found
#
            mc = re.search(obsidrev, ent)
            if mc is not None:
#
#--- if pos == 0, remove the submitted data entirely
#
                if pos == 0:
                    cmd = 'rm -rf ' + ocat_dir + '/updates/' + obsidrev
                    os.system(cmd)
                    continue
#
#--- otherwise, just revert the signoff
#
                atemp = re.split('\t+', ent)
                if pos == 1:
                    atemp[1] = 'NA'
                elif pos == 2:
                    atemp[2] = 'NA'
                elif pos == 3:
                    atemp[3] = 'NA'
                elif pos == 4:
                    atemp[4] = 'NA'
#
#--- when you reverse "verified by", check also other entries
#--- if other entries are 'N/A', it means that it was signed-off by the 
#--- person who verified; so reverse them to 'NA'
#
                elif pos == 5:
                    atemp[5] = 'NA'
                    for k in range(1, 4):
                        if atemp[k] == 'N/A':
                            atemp[k] = 'NA'
#
#--- if pos is 6, it means the submission was 'asis' verified by
#
                elif pos == 6:
                    atemp[5] = 'NA'

                line = atemp[0]
                for k in range(1, 8):
                    line = line + '\t' + atemp[k]
             
                save.append(line)
                chk = 1
#
#--- otherwise, just keep the data line as it is
#
            else:
                save.append(ent)
        else:
            save.append(ent)
#
#--- data are newest to oldest; so reverse the order before printing
#
    save.reverse()
    line = ''
    for ent in save:
        line = line + ent + '\n'
#
#--- check whether the file is currently not updated by the other user; 
#--- if it is open, lock the file and  proceed the changes
#
    if ocf.is_file_locked(updates_file):
        return True
    else:
        lock = threading.Lock()
        with lock:
            if float(os.path.getsize(updates_file)) > 0:
                cmd   = 'cp -f ' + updates_file + ' ' + updates_file + '~'
                os.system(cmd)

            with open(updates_file, 'w') as fo:
                fo.write(line)
#
#--- if this is 'asis' case, and verified by sign-off is reversed, also reverse approved list 
# 
    if pos == 6:
#
#--- check whether the file is locked, if not lock it for writing
#
        if ocf.is_file_locked(approve_file):
            return True

        else:
            lock = threading.Lock()
            data = ocf.read_data_file(approve_file)
            with lock:
                with open(approve_file, 'w') as fo:
                    line = write_approved_file(data, obsidrev)
                    fo.write(line)

    return False
                
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
#-- convert_display_time_to_chandra: convert data fomat from <mm>/<dd>/<yy> to chadra time
#----------------------------------------------------------------------------------

def convert_display_time_to_chandra(ltime):
    """
    convert data fomat from <mm>/<dd>/<yy> to chadra time
    input:  ltime   --- time in <mm>/<dd>/<yy>
            ctime   --- time in secs from 1998.1.1
    """
    ltime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(ltime, '%m/%d/%y'))
    ctime = int(Chandra.Time.DateTime(ltime).secs)

    return ctime

#----------------------------------------------------------------------------------
#-- create_display_data: create a table data of the last 10 entries              --
#----------------------------------------------------------------------------------

def create_display_data(data):
    """
    create a table data of the last 10 entries for the case no entries to reverse sign-off status
    input:  data    --- a list format of updates_table.list
    output: data_list   --- a list of lists:
                            [<obsidrev>,<general>, <acis>, <acis si>, <hrc si>,
                             <verified>, <seq nbr>, <poc>]
    """
    data_list = []
    for k in range(0, 10):
        atemp = re.split('\t+', data[k])
        data_list.append([atemp, 10])

    data_list.reverse()

    return data_list
        
#----------------------------------------------------------------------------------
#-- send_notification: sending removal from approved list                        --
#----------------------------------------------------------------------------------

def send_notification(obsid):
    """
    sending removal from approved list
    input:  obsid   --- obsid
    output: email sent out
    """
    sender    = 'cus@cfa.harvard.edu'
    recipient = current_user.email
    subject   = str(obsid) + ' is removed from approved list'

    text      = 'Remove Accidental Submission Page removed ' + str(obsid) 
    text      = text + ' from approved list.\n'

    if current_app.config['DEVELOPMENT']:
        email.send_email(subject, sender, recipient, text)
    else:
        email.send_email(subject, sender, recipient, text, bcc=bcc)

    
