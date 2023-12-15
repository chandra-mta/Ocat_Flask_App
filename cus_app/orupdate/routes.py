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
import threading

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
"""
p_file  = os.path.join(basedir, '../static/dir_list')
with  open(p_file, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec("%s = '%s'" %(var, line))
"""

s_dir    = os.path.join(basedir, '../static/')
#
#--- current chandra time
#
now    = int(Chandra.Time.DateTime().secs)
today  = ocf.convert_chandra_time_to_display2(now, tformat='%m/%d/%y')

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
#--- after 10 mins, don't dispaly the message, even if someone modified the
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
    input:  none but read from ocat_dir/updates_table.list
    output: odata   --- a list of data which need to be sign off
            cdata   --- a list of data which are already signed off
            mtime   --- the last file modified time stamp in Chandra Time
            poc_dict    --- a dict of <obsidrev> <---> <poc>
    """
    #
    #--- Main database file
    #
    ufile = os.path.join(current_app.config['OCAT_DIR'], 'updates_table.list')
    data  = ocf.read_data_file(ufile)
    data.reverse()
#
#--- find out the last file modification time
#
    mtime = ocf.find_file_modification_time(ufile)

    odata  = []                 #--- keep open data
    cdata  = []                 #--- keep closed data
    c_dict = {}                 #--- a dict to keep all opened rev # of <obsid>
    h_dict = {}                 #--- a dict to keep highest closed rev # of <obsid>
    r_dict = {}                 #--- a dict to keep highest  rev # of <obsid>
    poc_dict  = {}              #--- a dict to keep obsidrev <--> poc
#
#--- limit data for the last 400 entries
#
    for k in range(0, 400):
        ent   = data[k]
        atemp = re.split('\s+', ent)
        btemp = re.split('\.', atemp[0])
        obsid = btemp[0]
        rev   = int(float(btemp[1]))
#
#--- <obsid.rev> still needs sign-off
#
        mc    = re.search('NA', ent)
        if mc is not None:
            out = check_status(ent)
            odata.append(out)
            poc_dict[out[0]] = out[-1]
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
#--- <obsid>.<rev> which is already signed-off
#
        else:
#
#--- find out highest signed-off rev #  of each obsid
#
            if obsid in h_dict.keys():
                prev = float(h_dict[obsid])
                if  rev > prev:
                    h_dict[obsid] = ocf.add_leading_zero(rev, 3)
            else:
                h_dict[obsid] = ocf.add_leading_zero(rev, 3)
#
#--- check the signed-off date is in the specified period
#--- if so keep the record
#                
            chk = check_sign_off_date(ent)
            if chk == 1:
                out = check_status(ent)
                cdata.append(out)
                poc_dict[out[0]] = out[-1]
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

def check_status(line):
    """
    create data list
    input:  line    --- a row data read from updates_table.list
    output: data    --- a list of data, inclusing note section
                        <obsid>.<rev>
                        <sequence number>
                        <data creation date in mm/dd/yy>
                        <poc>
                        <general sign off status>
                        <acis sign off status>
                        <acis si sign off status>
                        <hrc si sign off status>
                        <verified by>
                        [a list of note section indicator (see blow)]
    """
    atemp    = re.split('\t+', line)
    obsidrev = atemp[0]
    gen      = atemp[1]
    acis     = atemp[2]
    acis_si  = atemp[3]
    hrc_si   = atemp[4]
    verify   = atemp[5]

    sqr_nbr  = atemp[6]
    poc      = atemp[7]
#
#--- date in <mm>/<dd>/<yy> format
#
    date     = check_file_creation_date(obsidrev)

    data     = [obsidrev, sqr_nbr, date, poc]

    data.append(gen)
    data.append(acis)
    data.append(acis_si)
    data.append(hrc_si)
    data.append(verify)
#
#--- add note saver list: note section will be filled later
#--- [<multiple obsidrev open>,<higher rev signed-off>,[<other comments>], 
#---  <grouped obsid color>, <new comment?>, <a large ccoordindate shift?>]
#
    data.append([0, 0, [], 'rgb(252, 226, 192, 0.3)', 0, 0])

    return data

#----------------------------------------------------------------------------------
#-- check_file_creation_date: find a file creation date                          --
#----------------------------------------------------------------------------------

def check_file_creation_date(obsidrev):
    """
    find a file creation date
    input:  obsidrev    --- <obsid>.<rev #>
    output: ltime       --- a creation time in <mm>/<dd>/<yy>
    """
    ifile = os.path.join(current_app.config['OCAT_DIR'], 'updates', str(obsidrev))
    stime = ocf.find_file_creation_time(ifile)
    out   = Chandra.Time.DateTime(stime).date
    atemp = re.split('\.', out)
    ltime = atemp[0]
    ltime = time.strftime('%m/%d/%y', time.strptime(ltime, '%Y:%j:%H:%M:%S'))
    
    return ltime

#----------------------------------------------------------------------------------
#-- check_sign_off_date: check whether this observation was signed off in a specified time period
#----------------------------------------------------------------------------------

def check_sign_off_date(line):
    """
    check whether this observation was signed off in a specified time period
    input:  line    --- data line
    output: 1: if yes, 0, otherwise
    """
    atemp = re.split('\t+', line)
    out   = atemp[5]
    btemp = re.split('\s+', out)
    sdate = btemp[1]   
    ltime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(sdate, '%m/%d/%y'))
    stime = Chandra.Time.DateTime(ltime).secs

    diff  = now - stime
    if diff < 129600:
        return 1
    else:
        return 0

#----------------------------------------------------------------------------------
#-- update_notes: create a content of the note section                          ---
#----------------------------------------------------------------------------------

def update_notes(odata, c_dict, h_dict, r_dict):
    """
    create a content of the note section
    input:  odata   --- a list of lists of data; the note section is the last part
                    <bsidrev open>,<higher rev signed-off>,[<other comments>], 
                    <color>, <new comment?>, <a large ccoordindate shift?>]
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
    coord_shift = ocf.read_data_file(ifile)
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
    data  = ocf.read_data_file(ifile)
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
        val      = atemp[0] + '.' + ocf.add_leading_zero(val, 3)
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
#-- check_signoff: update updates_table.list file according to which sign-off is clicked
#----------------------------------------------------------------------------------

def check_signoff(form, poc_dict, odata):
    """
    update updates_table.list file according to which sign-off is clicked
    this also update approved list and create a record file in 
    <ocat_dir>/updates/<obsid>.<rev#> if approved is requested
    input:  form        --- form data
            poc_dict    --- a dict of <obsidrev> <---> <poc>
    output: updated <ocat_dir>/updates_table.list
                    <ocat_dir>/approved
                    <ocat_dir>/updates/<obsid>.<rev>
            Ture/False  --- if updates_table.list was modified by someone else while
                           checking data, return True to warn the modificaiton. 
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
        mc7 = re.search('close',   key)
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
                chk = update_data(obsidrev, 1)
#
#--- acis is signed off
#
        elif mc2 is not None:
            obsidrev = get_obsidrev(key, form)
            if obsidrev != 0:
                chk = update_data(obsidrev, 2)
                if chk == False:
                    check_too_ddt(obsidrev, 'acis', odata, poc_dict[obsidrev])
#
#--- acis si is signed off
#
        elif mc3 is not None:
            obsidrev = get_obsidrev(key, form)
            if obsidrev != 0:
                chk = update_data(obsidrev, 3)
                if chk == False:
                    check_too_ddt(obsidrev, 'si', odata, poc_dict[obsidrev])
#
#--- hrc si is signed off
#
        elif mc4 is not None:
            obsidrev = get_obsidrev(key, form)
            if obsidrev != 0:
                chk = update_data(obsidrev, 4)
                if chk == False:
                    check_too_ddt(obsidrev, 'si', odata, poc_dict[obsidrev])
#
#--- verification is signed off
#
        elif mc5 is not None:
            obsidrev = get_obsidrev(key, form)
            if obsidrev != 0:
                chk = update_data(obsidrev, 5)
#
#--- vierification is signed off and approval is requested
#
        elif mc6 is not None:
            obsidrev = get_obsidrev(key, form)
            if obsidrev != 0:
                chk = update_data(obsidrev, 5)
                approve_obsid(obsidrev)

#
#--- closing of the <obisd>.<rev> is requested
#
        elif mc7 is not None:
            obsidrev = get_obsidrev(key, form)
            if obsidrev != 0:
                chk = update_data(obsidrev, 5, close=1)

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
    if ent in ['Sign-off', 'Sign-off & Approve', 'Close']:
        atemp = re.split('_', key)
        obsidrev = atemp[-1]
    else: 
        obsidrev = 0

    return obsidrev

#----------------------------------------------------------------------------------
#-- update_data: update <ocat_dir>/updates_table.list data file                   --
#----------------------------------------------------------------------------------

def update_data(obsidrev, pos, close=0):
    """ 
    update <ocat_dir>/updates_table.list data file
    input:  obsidrev    --- <obsid>.<rev#>
            pos         --- position of sign-off
                            1: general      --> col 1 
                            2: acis         --> col 2
                            3: acis si      --> col 3
                            4: hrc si       --> col 4
                            5: verified by  --> col 5
                            note: col 0 is <obsid>.<rev>
                                  col 6 is <seq #>
                                  col 7 is <poc id>
            close       --- whehter close is asked or not 0/1 . 1: yes
    output: updated <ocat_dir>/updates_table.list
    """
    user     = current_user.username    
    sign     = user + ' ' + today
    obsidrev = str(obsidrev)
    #
    #--- Main database file
    #
    ufile = os.path.join(current_app.config['OCAT_DIR'], 'updates_table.list')
#
#--- check whether the file is locked. if not lock the file for this round
#
    if ocf.is_file_locked(ufile):
        return True 
    else:
#
#--- update the data file
#
        data = ocf.read_data_file(ufile)
        lock = threading.Lock()
        with lock:
            with open(ufile, 'w') as fo:
                cmd = 'cp  -f ' + ufile + ' ' + ufile + '~'
                os.system(cmd)

                line = create_data_line(data, obsidrev, pos, sign, close)
                fo.write(line)

        return False

#----------------------------------------------------------------------------------
#-- create_data_line: create data line to print out                              --
#----------------------------------------------------------------------------------

def create_data_line(data, obsidrev, pos, sign, close):
    """
    create data line to print out
    input:  data        --- a list of data
            obsidreve   --- <obsid>.<rev #>
            pos         --- position of sign-off
            sign        --- <user name> <today's date>
            close       --- 0/1. if 1, close all open sign-off
    output: line        --- strings of output data
    """
    dlen     = len(data)
#
#--- reverse the data; assume that none-closed entries are at the close to the end 
#
    data.reverse()
    for k in range(0, dlen):
        ent   = data[k]
        atemp = re.split('\t+', ent)
        if atemp[0] == obsidrev:
            atemp[pos] = sign
#
#--- if closing is asked, fill opened column with 'N/A' (except verified column)
#
            if close > 0:
                for m in range(1, 5):
                    if atemp[m] == 'NA':
                        atemp[m] = 'N/A'
    
            line = atemp[0] + '\t' + atemp[1] + '\t' + atemp[2] 
            line = line     + '\t' + atemp[3] + '\t' + atemp[4]
            line = line     + '\t' + atemp[5] + '\t' + atemp[6]
            line = line     + '\t' + atemp[7] 
            data[k] = line
            break

    data.reverse()

    line = ''
    for ent in data:
        if ent == '':
            continue
        else:
            line = line + ent + '\n'

    return line

#----------------------------------------------------------------------------------
#-- approve_obsid: approve the obsid                                             --
#----------------------------------------------------------------------------------

def approve_obsid(obsidrev):
    """
    approve the obsid 
    input:  obsidrev    --- <obsid>.<rev#>
    output: <ocat_dir>/approve
            <ocat_dir>/updates/<obsid>.<rev# + 1>
            various email send out 
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
    output: email sendt out
    """
    sender  = 'cus@cfa.harvard.edu'
    bcc     = 'cus@cfa.harvard.edu'
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
                text = text + "Please  update SI Mode entries, then go to: " + current_app.config['HTTP_ADDRESS'] + 'orupdate'
                text = text + "and sign off SI Mode Status.\n"

                subject = otype.upper() + ' SI Status Signed Off Request: OBSID: ' + obsid

                mc   = re.search('acis', inst.lower())
                if mc is not None:
                    recipient = 'acisdude@cfa.harvard.edu'
                else:
                    recipient = 'hrcdude@cfa.harvard.edu'
            else:
                text = "Editing of all entries of " + obsidrev + " were finished and signed off. "
                text = text + "Please  verify it, then go to: " + current_app.config['HTTP_ADDRESS'] + 'orupdate'
                text = text + "and sign off 'Verified By' column.\n"

                subject = otype.upper() + '  Verification Signed Off Request: OBSID: ' + obsid
#
#--- poc_list: a list of [<poc id>, < full name>, <emai address>]
#--- if poc id is provided, that entry will be place at the first of the list
#
                poc_list  = ocf.read_poc_list(poc)
                recipient = poc_list[0][2]
            
            if current_app.config['DEVELOPMENT']:
                recipient = current_user.email
                email.send_email(subject, sender, recipient, text)
            else:
                email.send_email(subject, sender, recipient, text, bcc=bcc)
#
#--- acis/hrc si mode column signed off
#
        elif colname == 'si':
            if gen == 'NA':
                text = "Editing of SI entries of " + obsidrev + " were finished and signed off. "
                text = text + "Please  update General/ACIS entries, then go to: " + current_app.config['HTTP_ADDRESS'] + 'orupdate'
                text = text + "and sign off SI Mode Status.\n"

                subject = otype.upper() + ' General/ACIS Status Signed Off Request: OBSID: ' + obsid

                recipient = 'arcops@cfa.harvard.edu'
            else:
                text = "Editing of all entries of " + obsidrev + " were finished and signed off. "
                text = text + "Please  verify it, then go to: " + current_app.config['HTTP_ADDRESS'] + 'orupdate'
                text = text + "and sign off 'Verified By' column.\n"

                subject = otype.upper() + '  Verification Signed Off Request: OBSID: ' + obsid

                poc_list  = ocf.read_poc_list(poc)
                recipient = poc_list[0][2]
            

            if current_app.config['DEVELOPMENT']:
                recipient = current_user.email
                email.send_email(subject, sender, recipient, text)
            else:
                email.send_email(subject, sender, recipient, text, bcc=bcc)

#----------------------------------------------------------------------------------
#-- read_status: find gen and si mode status of a given <obsidrev>               --
#----------------------------------------------------------------------------------

def read_status(obsidrev, odata):
    """
    find gen and si mode status of a given <obsidrev>
    input:  obsidrev    --- <obsid>.<rev>
            odata       --- a list of lists of data of each obsidrev
    output: gen         --- general status
            si          --- aics/hrc si mode status
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
