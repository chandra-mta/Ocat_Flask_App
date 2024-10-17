#################################################################################
#                                                                               #
#   target parameter update status page                                         #
#                                                                               #
#       author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                               #
#       last update: Sep 21, 2021                                               #
#                                                                               #
#################################################################################
import os
import sys
import re
import string
import Chandra.Time
import time
from datetime           import datetime
import pathlib
import threading
import sqlite3 as sq
import traceback
from contextlib import closing

from flask              import render_template, flash, redirect, url_for, session
from flask              import request, g, jsonify, current_app
from flask_login        import current_user

from cus_app                import db
from cus_app.models         import User, register_user 
from cus_app.orupdate       import bp

import cus_app.supple.ocat_common_functions         as ocf
import cus_app.supple.get_value_from_sybase         as gvfs
import cus_app.ocatdatapage.create_selection_dict   as csd
import cus_app.ocatdatapage.update_data_record_file as udrf
import cus_app.emailing                             as email
#
#--- directory
#
basedir = os.path.abspath(os.path.dirname(__file__))
s_dir    = os.path.join(basedir, '../static/')
#
#--- Define Globals
#
TODAY = datetime.now()
TODAY_STRING = TODAY.strftime('%m/%d/%y')
FETCH_SIZE = 400

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
#-- index: this is the main function to display orupdate page                    --
#----------------------------------------------------------------------------------

@bp.route('/',      methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    current_app.logger.info(f"Opening Orupdate")
    user         = current_user.username
#
#--- odata --- a list of open data
#--- cdata --- a list of signed-off data within the past one day
#--- mtime --- a time stamp of the last database updated 
#--- warning will be True if someone just updated database files
#
    odata, cdata, mtime, poc_dict = read_status_data()
    warning                       = False

    if 'submit_test' in request.form:
#
#--- display order change request is submitted
#
        if 'ordered_by' in  request.form.keys():
            odata = check_order_request(request.form, odata)
#
#--- sign-off reqeust is submitted
#
        else:
#
#--- check whether someone updated the database while the user was checking 
#--- the entries if it happened, display the warning without the updates.
#
            ctime = float(request.form['mtime'])
            if mtime > ctime:
#
#--- after 10 mins, don't display the message, even if someone modified the
#--- the database before submitting the data.
#
                if Chandra.Time.DateTime().secs - mtime < 700.0:
                    warning = True
            else:
                warning = check_signoff(request.form, poc_dict, odata)

            odata, cdata, mtime, poc_dict = read_status_data()

    return render_template('orupdate/index.html',
                            user  = user,
                            odata = odata,
                            cdata = cdata,
                            mtime = mtime,
                            warning = warning,
                            current_user = current_user
                            )

#----------------------------------------------------------------------------------
#-- read_status_data: read the data base and create a list of data               --
#----------------------------------------------------------------------------------

def read_status_data():
    """
    read the data base and create a list of data
    input:  none but read from ocat_dir/updates_table.db
    output: odata   --- a list of data which need to be sign off
            cdata   --- a list of data which are already signed off
            mtime   --- the last file modified time stamp in Chandra Time
            poc_dict    --- a dict of <obsidrev> <---> <poc>
    """
#
#--- Main database file
#--- Also find out the last file modification time
#
    ufile = os.path.join(current_app.config['OCAT_DIR'], 'updates_table.db')
    mtime = ocf.find_file_modification_time(ufile)
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
    odata  = []                 #--- keep open data
    cdata  = []                 #--- keep closed data
    c_dict = {}                 #--- a dict to keep all opened rev # of <obsid>
    h_dict = {}                 #--- a dict to keep highest closed rev # of <obsid>
    r_dict = {}                 #--- a dict to keep highest  rev # of <obsid>
    poc_dict  = {}              #--- a dict to keep obsidrev <--> poc
#
#--- Iterate over the fetch results
#
    for entry in fetch_result:
        obsid, rev = str(entry[0]).split('.')
        rev = int(rev)
#
#--- Generate opened/closed sublists and check if a signoff is still required
#
        sublist, opened = check_status(entry)
        if opened:
            odata.append(sublist)
            poc_dict[sublist[0]] = sublist[3]
#
#--- prep to check multiple opening of the same obsid
#
            if obsid in c_dict.keys():
                c_dict[obsid]  = c_dict[obsid] + 1

            else:
                c_dict[obsid] = 1
                if not (obsid in h_dict.keys()):
                    h_dict[obsid] = 0
#
#--- <obsid>.<rev> which is already signed-off and closed
#
        else:
#
#--- find out highest signed-off rev #  of each obsid
#
            if obsid in h_dict.keys():
                prev = float(h_dict[obsid])
                if  rev > prev:
                    h_dict[obsid] = f"{rev:>03}"
            else:
                h_dict[obsid] = f"{rev:>03}"
#
#--- check the signed-off date is in the specified period
#--- if so keep the record for informational display
#
            if (TODAY - datetime.strptime(entry[10],'%m/%d/%y')).days < 2:
                cdata.append(sublist)
                poc_dict[sublist[0]] = sublist[3]
#
#--- find out highest  rev #  of each obsid
#
        if obsid in r_dict.keys():
            prev = r_dict[obsid]
            if  rev > prev:
                r_dict[obsid] = rev
        else:
            r_dict[obsid] = rev
#
#--- update note sections of open entries
#
    odata = update_notes(odata, c_dict, h_dict, r_dict)
    return odata, cdata, mtime, poc_dict

#----------------------------------------------------------------------------------
#-- check_status: create data list                                               --
#----------------------------------------------------------------------------------

def check_status(entry):
    """
    create data list
    input:  entry   --- an SQL data row read from updates_table.db
    output: data    --- a list of data, including a note section and an indicator of opened of closed.
                        <obsid>.<rev>
                        <sequence number>
                        <data creation date in mm/dd/yy>
                        <poc>
                        <general sign off status>
                        <acis sign off status>
                        <acis si sign off status>
                        <hrc si sign off status>
                        <verified by>
                        [a list of note section indicator (see below)]
    """
#
#--- In the process of recording signoff status in the template parseable lists,
#--- we can set an opened/closed boolean
#
    opened = False
    sublist = [str(entry[0]), str(entry[11]), datetime.fromtimestamp(entry[13]).strftime("%m/%d/%y"), entry[12]]
#
#--- general signoff
#
    if entry[1] == 'NA':
        opened = True
        sublist.append(entry[1])
    elif entry[1] == 'N/A':
        sublist.append(entry[1])
    elif entry[1] == None:
        sublist.append('NULL')
    else:
        sublist.append(f"{entry[1]} {entry[2]}")
#
#--- acis signoff
#  
    if entry[3] == 'NA':
        opened = True
        sublist.append(entry[3])
    elif entry[3] == 'N/A':
        sublist.append(entry[3])
    elif entry[3] == None:
        sublist.append('NULL')
    else:
        sublist.append(f"{entry[3]} {entry[4]}")
#
#--- acis si mode signoff
#
    if entry[5] == 'NA':
        opened = True
        sublist.append(entry[5])
    elif entry[5] == 'N/A':
        sublist.append(entry[5])
    elif entry[5] == None:
        sublist.append('NULL')
    else:
        sublist.append(f"{entry[5]} {entry[6]}")
#
#--- hrc si mode signoff
#
    if entry[7] == 'NA':
        opened = True
        sublist.append(entry[7])
    elif entry[7] == 'N/A':
        sublist.append(entry[7])
    elif entry[7] == None:
        sublist.append('NULL')
    else:
        sublist.append(f"{entry[7]} {entry[8]}")
#
#--- usint verification
#
    if entry[9] == 'NA':
        opened = True
        sublist.append(entry[9])
    elif entry[9] == 'N/A':
        sublist.append(entry[9])
    elif entry[9] == None:
        sublist.append('NULL')
    else:
        sublist.append(f"{entry[9]} {entry[10]}")
#
#--- add note saver list: note section will be filled later
#--- [<multiple obsidrev open>,<higher rev signed-off>,[<other comments>], 
#---  <grouped obsid color>, <new comment?>, <a large ccoordindate shift?>]
#
    sublist.append([0, 0, [], 'rgb(252, 226, 192, 0.3)', 0, 0])
    return sublist, opened

#----------------------------------------------------------------------------------
#-- check_file_creation_date: find a file creation date                          --
#----------------------------------------------------------------------------------

def check_file_creation_date(obsidrev):
    """
    find a file creation date
    input:  obsidrev    --- <obsid>.<rev #>
    output: mtime       --- a creation time in <mm>/<dd>/<yy>
    """
    ifile = os.path.join(current_app.config['OCAT_DIR'], 'updates', str(obsidrev))
    if os.path.isfile(ifile):
        fname = pathlib.Path(ifile)
        mtime = datetime.fromtimestamp(fname.stat().st_ctime)
        return mtime.strftime("%m/%d/%y")

#----------------------------------------------------------------------------------
#-- update_notes: create a content of the note section                          ---
#----------------------------------------------------------------------------------

def update_notes(odata, c_dict, h_dict, r_dict):
    """
    create a content of the note section
    input:  odata   --- a list of lists of data; the note section is the last part
                    <obsidrev open>,<higher rev signed-off>,[<other comments>], 
                    <color>, <new comment?>, <a large coordindate shift?>]
            c_dict  --- a dict of <obsid> <---> <rev # still open>
            h_dict  --- a dict of <obsid.rev> <---> <rev # of highest signoff obsid.rev>
                                                     in string format
            r_dict  --- a dict of <obsid.rev> <---> <rev # of highest obsid.rev>
                                                     in integer
    output: odata   --- an update data list
    """
#
#--- read color list and set opacity to 0.3
#
    color_list  = read_color_list(opacity=0.3)
#
#--- read large coordinate shift data
#
    ifile       = os.path.join(current_app.config['OCAT_DIR'], 'cdo_warning_list')
    with open(ifile,'r') as f:
        coord_shift = [line.strip() for line in f.readlines()]
    coord_shift.reverse()
#
#--- give the same color to the same obsid (ignore rev #)
#
    o_list = list(c_dict.keys())
    o_len  = len(o_list)
    c_len  = len(color_list)
    p_dict = {}
    for k in range(0, o_len):
#
#--- just in a case when the # of obsids is larger than the # of color list
#
        m  = k - c_len * int(k / c_len)
        p_dict[o_list[k]] = color_list[m]

    for k in range(0, len(odata)):
        ent   = odata[k]
        atemp = re.split('\.', ent[0])
        obsid = atemp[0]
        rev   = int(float(atemp[1]))
#
#--- multiple obsid sign off still open?
#--- code = 0: no other revision open
#--- code = 1: there are multiple revisions but this is the latest revision
#--- code = 2: there are multiple revisions and there is a newer revision than this one
#
        if c_dict[obsid] > 1:
            if rev < r_dict[obsid]:
                ent[-1][0] = 2
            else:
                ent[-1][0] = 1
            ent[-1][3] = p_dict[obsid]
#
#--- higher obsid.rev is already signed off?
#
        if float(h_dict[obsid]) > rev:
            ent[-1][1] = h_dict[obsid]
#
#--- a new comment?
#
        ent[-1][4] = check_comment(ent[0])
#
#--- a large coordinate shifts?
#
        ent[-1][5] = check_large_coord_shift(ent[0], coord_shift)

        odata[k] = ent

    return  odata

#----------------------------------------------------------------------------------
#-- check_comment: check whether ths entry has a new comment                     --
#----------------------------------------------------------------------------------

def check_comment(obsidrev):
    """
    check whether ths entry has a new comment
    input:  obsidrev    --- <obsid>.<rev #>
    outpu:  1 if there is a large coordinate shift, otherwise, 0
    """
    ifile = os.path.join(current_app.config['OCAT_DIR'], 'updates', str(obsidrev))
    #If data directory corrupted/missing revision file, bigger problems exist
    #yet this comment check can act as a safety check.
    try:
        with open(ifile, 'r') as f:
            text = f.read()
    except Exception as check_comment_exc:
        return 2

    mc = re.search('NEW COMMENTS', text)
    if mc is not None:
        return 1
    else:
        return 0

#----------------------------------------------------------------------------------
#-- check_large_coord_shift: check a large coordinate shift                     ---
#----------------------------------------------------------------------------------

def check_large_coord_shift(obsidrev, coord_shift):
    """
    check a large coordinate shift
    input:  obsidrev    --- <obsid>.<rev #>
            coord_shift --- a list or obsid.rev with a large coordindate shift
    outpu:  1 if there is a large coordinate shift, otherwise, 0
    """
    for comp in coord_shift:
        if obsidrev  == comp:
            return 1
    
    return 0

#----------------------------------------------------------------------------------
#-- read_color_list: read color table                                            --
#----------------------------------------------------------------------------------

def read_color_list(name=0, opacity=1):
    """
    read color table
    input:  name        --- if 0, rgb color name/1: literal color name
            opacity     --- opacity of the color; only work with rgb
    output: color_list  --- a list of colors
    """
    ifile = s_dir + 'color_list'
    with open(ifile,'r') as f:
        data = [line.strip() for line in f.readlines()]
    color_list = []

    for ent in data:
        atemp = re.split(':', ent)
        if name == 1:
            color = atemp[0].strip()
        else:
            color = atemp[1].strip()
            part  = ', ' + str(opacity) + ')'
            color = color.replace(')', part)

        color_list.append(color)

    return color_list

#----------------------------------------------------------------------------------
#-- check_order_request: modify the display order                               ---
#----------------------------------------------------------------------------------

def check_order_request(form, odata):
    """
    modify the display order
    input:  form    --- form data
            odata   --- a list of data
    ouput:  odata   --- a re-ordered list of data
    """
    if form['ordered_by'] == 'Date of Submission':
        odata = ordered_by_date(odata)

    elif form['ordered_by'] == 'Obsid':
        odata = ordered_by_obsid(odata)

    elif form['ordered_by'] == 'User ID:':
        user = form['ordered_by_user']
        user = user.strip()
        odata = ordered_by_userid(odata, user)

    return odata

#----------------------------------------------------------------------------------
#-- ordered_by_date: change the display order by date from the newest to oldest  --
#----------------------------------------------------------------------------------

def ordered_by_date(odata):
    """
    change the display order by date from the newest to oldest
    input:  odata   --- a list of data
    output: odata   --- a re-ordered list of data
    """
    d_list = []
    for ent in odata:
        date  = ent[2]
        atemp = re.split('\/', date)
        date  = atemp[2] + atemp[0] + atemp[1]
        date  = int(date)
        d_list.append(date)

    out = [x for _, x in sorted(zip(d_list, odata))]
    out.reverse()

    return out

#----------------------------------------------------------------------------------
#-- ordered_by_obsid: change the display order by obsid                         ---
#----------------------------------------------------------------------------------

def ordered_by_obsid(odata):
    """
    change the display order by obsid
    input:  odata   --- a list of data
    output: odata   --- a re-ordered list of data
    """
    d_list = []
    for ent in odata:
        obsidrev = ent[0]
#
#--- reversing rev # order so that the largest/newest revision come to top
#
        atemp    = re.split('\.', obsidrev)
        val      = 100 - int(float(atemp[1]))
        val = f"{atemp[0]}.{val:>03}"
        d_list.append(float(val))

    out = [x for _, x in sorted(zip(d_list, odata))]

    return out

#----------------------------------------------------------------------------------
#-- ordered_by_userid: bring groups of obsids owned by the user to top           --
#----------------------------------------------------------------------------------

def ordered_by_userid(odata, user):
    """
    bring groups of obsids owned by the user to top
    input:  odata   --- a list of data
    output: odata   --- a re-ordered list of data
    """
    top    = []
    others = []

    for ent in odata:
        poc = ent[3].strip()
        if poc == user:
            top.append(ent)
        else:
            others.append(ent)
#
#--- order them in the order of obsid
#
    top = ordered_by_obsid(top)
    out = top + others

    return out

#----------------------------------------------------------------------------------
#-- check_signoff: update updates_table.db file according to which sign-off is clicked
#----------------------------------------------------------------------------------

def check_signoff(form, poc_dict, odata):
    """
    update updates_table.db file according to which sign-off is clicked
    this also update approved list and create a record file in 
    <ocat_dir>/updates/<obsid>.<rev#> if approved is requested
    input:  form        --- form data
            poc_dict    --- a dict of <obsidrev> <---> <poc>
    output: updated <ocat_dir>/updates_table.db
                    <ocat_dir>/approved
                    <ocat_dir>/updates/<obsid>.<rev>
            Ture/False  --- if updates_table.db was modified by someone else while
                           checking data, return True to warn the modification. 
                           otherwise, return False
    """
    for key in form.keys():
        mc = re.search('ordered', key)
        if mc is not None:
            continue
#
#--- no one modified the file; so we can procced update
#
        mc1 = re.search('gen',     key)
        mc2 = re.search('acis',    key)
        mc3 = re.search('si',      key)
        mc4 = re.search('hrc',     key)
        mc5 = re.search('verify',  key)
        mc6 = re.search('approve', key)
        mc7 = re.search('discard',   key)
        chk = False
#
#--- general is signed off
#
        if mc1 is not None:
            obsidrev = get_obsidrev(key, form)
            if obsidrev != 0:
#
#--- chk is True, if someone just updated the database file and the user
#--- could not update the database files
#
                chk = update_data(obsidrev, 'general_signoff')
#
#--- acis is signed off
#
        elif mc2 is not None:
            obsidrev = get_obsidrev(key, form)
            if obsidrev != 0:
                chk = update_data(obsidrev, 'acis_signoff')
                if chk == False:
                    check_too_ddt(obsidrev, 'acis', odata, poc_dict[obsidrev])
#
#--- acis si is signed off
#
        elif mc3 is not None:
            obsidrev = get_obsidrev(key, form)
            if obsidrev != 0:
                chk = update_data(obsidrev, 'acis_si_mode_signoff')
                if chk == False:
                    check_too_ddt(obsidrev, 'si', odata, poc_dict[obsidrev])
#
#--- hrc si is signed off
#
        elif mc4 is not None:
            obsidrev = get_obsidrev(key, form)
            if obsidrev != 0:
                chk = update_data(obsidrev, 'hrc_si_mode-signoff')
                if chk == False:
                    check_too_ddt(obsidrev, 'si', odata, poc_dict[obsidrev])
#
#--- verification is signed off
#
        elif mc5 is not None:
            obsidrev = get_obsidrev(key, form)
            if obsidrev != 0:
                chk = update_data(obsidrev, 'usint_verification')
#
#--- vierification is signed off and approval is requested
#
        elif mc6 is not None:
            obsidrev = get_obsidrev(key, form)
            if obsidrev != 0:
                chk = update_data(obsidrev, 'usint_verification')
                approve_obsid(obsidrev)

#
#--- closing of the <obisd>.<rev> is requested
#
        elif mc7 is not None:
            obsidrev = get_obsidrev(key, form)
            if obsidrev != 0:
                chk = update_data(obsidrev, 'discard')

    return chk

#----------------------------------------------------------------------------------
#-- get_obsidrev: extract <obsid>.<rev> from form data submitted                ---
#----------------------------------------------------------------------------------

def get_obsidrev(key, form):
    """
    extract <obsid>.<rev> from form data submitted
    the key of the form data for the submission has a format of:
        <type of submission>_<obsid.rev>
    input:  key     --- key of the form data
            form    --- form data
    output: obsidrev #
    """
#
#--- only when the data value exists, return <obsid>.<rev#>
#
    ent = form[key]
    if ent in ['Sign-off', 'Sign-off & Approve', 'Discard']:
        atemp = re.split('_', key)
        obsidrev = atemp[-1]
    else: 
        obsidrev = 0

    return obsidrev

#----------------------------------------------------------------------------------
#-- update_data: update <ocat_dir>/updates_table.db data file                   --
#----------------------------------------------------------------------------------

def update_data(obsidrev, column_signoff):
    """ 
    update <ocat_dir>/updates_table.db data file
    input:  obsidrev    --- <obsid>.<rev#>
            column_signoff --- selection of column to put in signoff. If discard, then do special discard action
    output: updated <ocat_dir>/updates_table.db
    """
#
#--- Main database file
#
    ufile = os.path.join(current_app.config['OCAT_DIR'], 'updates_table.db')
    try:
        with closing(sq.connect(ufile)) as conn: # auto-closes
            with conn: # auto-commits
                with closing(conn.cursor()) as cur: # auto-closes
                    if column_signoff == 'discard':
#
#--- Pull the current signoff status and replace any unfilled signoffs with "N/A"
#
                        select_discard = f'SELECT general_signoff, acis_signoff, acis_si_mode_signoff, hrc_si_mode_signoff from revisions WHERE obsidrev = {obsidrev}'
                        res = cur.execute(select_discard)
                        curr_signoff = res.fetchone()
                        discard_execute = f'UPDATE revisions SET general_signoff = "{curr_signoff[0]}", acis_signoff = "{curr_signoff[1]}", acis_si_mode_signoff = "{curr_signoff[2]}", hrc_si_mode_signoff = "{curr_signoff[3]}", usint_verification = "{current_user.username}", usint_date = "{TODAY_STRING}" WHERE obsidrev = {obsidrev}'
                        discard_execute = discard_execute.replace('NA','N/A').replace('"None"','NULL')
                        if current_app.config['DEVELOPMENT']:
                            print(select_discard)
                            print(discard_execute)
                        cur.execute(discard_execute)
                    else:
#
#--- Update signoff column and date
#
                        date_col = column_signoff.replace("_signoff","_date").replace("_verification","_date")
                        update_execute = f'UPDATE revisions SET {column_signoff} = "{current_user.username}", {date_col} = "{TODAY_STRING}" WHERE obsidrev = {obsidrev}'
                        if current_app.config['DEVELOPMENT']:
                            print(update_execute)
                        cur.execute(update_execute)
        return False
    except sq.OperationalError:
        current_app.logger.error(traceback.format_exc())
        email.send_error_email()
        return True

#----------------------------------------------------------------------------------
#-- approve_obsid: approve the obsid                                             --
#----------------------------------------------------------------------------------

def approve_obsid(obsidrev):
    """
    approve the obsid 
    input:  obsidrev    --- <obsid>.<rev#>
    output: <ocat_dir>/approve
            <ocat_dir>/updates/<obsid>.<rev# + 1>
            various emails sent out 
    """
    asis  = 'asis'
    user  = current_user.username
    
    atemp = re.split('\.', obsidrev)
    obsid = atemp[0]
#
#--- read the parameter values from the database
#
    ct_dict  = csd.create_selection_dict(obsid)
#
#--- although no parameters are updated, we need the this dict which
#--- list which parameters are updated
#
    ind_dict = csd.create_match_dict(ct_dict)
#
#--- update the databases; two outputs, "changed_param" and "note" are not used
#
    changed_param, note = udrf.update_data_record_file(ct_dict, ind_dict, asis, user)

#----------------------------------------------------------------------------------
#-- check_too_ddt: sending TOO/DDT sign-off request email                        --
#----------------------------------------------------------------------------------

def check_too_ddt(obsidrev, colname, odata, poc=''):
    """
    sending TOO/DDT sign-off request email
    input:  obsidrev    --- <obsid>.<rev #>
            colname     --- name of the current column; either gen or si
            odata       --- a list of lists of data of each obsidrev
            poc         --- poc ID
    output: email sent out
    """
    sender  = 'cus@cfa.harvard.edu'
#
#--- get the type of observation and the instrument of obsid
#
    atemp   = re.split('\.', obsidrev)
    obsid   = atemp[0]

    cmd     = "select type, instrument from target where obsid=" + obsid
    out     = gvfs.get_value_from_sybase(cmd, 'axafocat')
    otype   = out[0][0]
    inst    = out[0][1]
#
#--- if the type is TOO or DDT, send out a notification
#
    if otype.lower() in ['too', 'ddt']:
#
#--- general and acis/si mode status
#
        gen, si = read_status(obsidrev, odata)
#
#--- general/acis sttus column signed off
#
        if colname == 'acis':
            if si == 'NA':
                text = "Editing of General/ACIS entries of " + obsidrev + " were finished and signed off. "
                text = text + "Please  update SI Mode entries, then go to: " + current_app.config['HTTP_ADDRESS'] + '/orupdate'
                text = text + " and sign off SI Mode Status.\n"

                subject = otype.upper() + ' SI Status Signed Off Request: OBSID: ' + obsid

                mc   = re.search('acis', inst.lower())
                if mc is not None:
                    recipient = 'acisdude@cfa.harvard.edu'
                else:
                    recipient = 'hrcdude@cfa.harvard.edu'
            else:
                text = "Editing of all entries of " + obsidrev + " were finished and signed off. "
                text = text + "Please  verify it, then go to: " + current_app.config['HTTP_ADDRESS'] + '/orupdate'
                text = text + " and sign off 'Verified By' column.\n"

                subject = otype.upper() + '  Verification Signed Off Request: OBSID: ' + obsid
#
#--- poc_list: a list of [<poc id>, < full name>, <emai address>]
#--- if poc id is provided, that entry will be place at the first of the list
#
                poc_list  = ocf.read_poc_list(poc)
                recipient = poc_list[0][2]
            
            email.send_email(subject, sender, recipient, text)
#
#--- acis/hrc si mode column signed off
#
        elif colname == 'si':
            if gen == 'NA':
                text = "Editing of SI entries of " + obsidrev + " were finished and signed off. "
                text = text + "Please  update General/ACIS entries, then go to: " + current_app.config['HTTP_ADDRESS'] + '/orupdate'
                text = text + " and sign off SI Mode Status.\n"

                subject = otype.upper() + ' General/ACIS Status Signed Off Request: OBSID: ' + obsid

                recipient = 'arcops@cfa.harvard.edu'
            else:
                text = "Editing of all entries of " + obsidrev + " were finished and signed off. "
                text = text + "Please  verify it, then go to: " + current_app.config['HTTP_ADDRESS'] + '/orupdate'
                text = text + " and sign off 'Verified By' column.\n"

                subject = otype.upper() + '  Verification Signed Off Request: OBSID: ' + obsid

                poc_list  = ocf.read_poc_list(poc)
                recipient = poc_list[0][2]
            

            email.send_email(subject, sender, recipient, text)

#----------------------------------------------------------------------------------
#-- read_status: find gen and si mode status of a given <obsidrev>               --
#----------------------------------------------------------------------------------

def read_status(obsidrev, odata):
    """
    find gen and si mode status of a given <obsidrev>
    input:  obsidrev    --- <obsid>.<rev>
            odata       --- a list of lists of data of each obsidrev
    output: gen         --- general status
            si          --- acis/hrc si mode status
    """
    gen  = 'NA'
    si   = 'NA'
    for ent in odata:
        if ent[0] == obsidrev:
            gen  = ent[4]
            acis = ent[5]
            hrc  = ent[6]
            if acis == 'NA' or hrc == 'NA':
                si = 'NA'
            else:
                si = 'NULL'

            break

    return gen, si
