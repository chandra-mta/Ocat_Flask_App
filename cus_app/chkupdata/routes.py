#########################################################################################
#                                                                                       #
#   chkupdata page: display all original/requsted/current parameter values for           #
#                   given <obsid>.<rev>                                                 #
#                                                                                       #
#       author: t.isobe (tisobe@cfa.harvard.edu)                                        #
#                                                                                       #
#       last upate: Sep 10, 2021                                                        #
#                                                                                       #
#########################################################################################

import os 
import sys
import re
import string
import time
from datetime import datetime
import Chandra.Time
import copy

from flask          import render_template, flash, redirect, url_for, session
from flask          import request, g, jsonify, current_app
from flask_login    import current_user

from cus_app            import db
from cus_app.models     import User, register_user
from cus_app.chkupdata  import bp
from cus_app.chkupdata.forms import SubmitForm

import cus_app.supple.ocat_common_functions     as ocf
import cus_app.supple.read_ocat_data            as rod
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
#
#--- read ocat parameter list
#
#basedir = os.path.abspath(os.path.dirname(__file__))
p_file  = os.path.join(basedir, '../static/param_list')
with open(p_file, 'r') as f:
    all_param_list = [line.strip() for line in f.readlines()]
#
#--- define a few data list
#
null_list  = [None, 'NA', 'NULL', 'None', 'null', 'none', '', '<Blank>']

time_list  = ['window_constraint', 'tstart', 'tstop']

roll_list  = ['roll_constraint', 'roll_180', 'roll', 'roll_tolerance']

awin_list  = ['chip', 'start_row', 'start_column', 'height',\
              'width', 'lower_threshold',   'pha_range',    'sample']

ordr_list  = time_list + roll_list + awin_list

#--------------------------------------------------------------------------
#-- before_request: this will be run before every time index is called   --
#--------------------------------------------------------------------------

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        session['session_start'] = int(Chandra.Time.DateTime().secs)
        session.permanent        = True
        session.modified         = True
    else:
        register_user()

#--------------------------------------------------------------------------
#-- index: this is the main function to display chkupdata page           --
#--------------------------------------------------------------------------

@bp.route('/',             methods=['GET', 'POST'])
@bp.route('/<name>',       methods=['GET', 'POST'])
@bp.route('/index/<name>', methods=['GET', 'POST'])
def index(name=''):
    current_app.logger.info(f"Opening Obsid.Rev: {name}")
#
#--- initialize
#
    d_dict    = {}              #--- a dict of param <---> param values
                                #--- (org, req, current, and status ind)
    p_list    = []              #--- a list of parameters
    gc_dict   = {}              #--- a dict of general parameter changes`
    ac_dict   = {}              #--- a dict of acis parameter changes
    awc_dict  = {}              #--- a dict of acis window parameter changes
    other_rev = []              #--- a list pf other revisions available

    stage     = 0               #--- an indicator of whether the data file exit 
                                #--- 0 means No
    form      = SubmitForm()    #--- <obsid>.<rev> submisison form (on try_again.html)
#
#--- check whether obsid.rev is updated/submitted (e.g., from try_again.html page)
#
    if form.validate_on_submit():
        name  = form.obsidrev.data
        return redirect(name) 
#
#--- the file name is given; check whether the file exists
#
    if name != '':
        out = get_data(name)
#
#--- the data file exists; read the data and pass the data to the template
#
        if out:
            d_dict    = out[0]   
            p_list    = out[1]
            gc_dict   = out[2]
            ac_dict   = out[3]
            awc_dict  = out[4]
            other_rev = out[5]
#
#--- set the indicator of the data existance to 1
#            
            stage     = 1
#
#--- if the data file does not exist, check other revs are available
#
        else:
            atemp     = re.split('\.', name)
            obsid     = atemp[0]
            other_rev = ocf.find_other_revisions(obsid)
#
#--- if the file does not exist, it will open "try_again.html" page
#--- otherwise, it will open "displya.html' page
#
    return render_template('chkupdata/index.html',     \
                                p_list    = p_list,    \
                                data      = d_dict,    \
                                gc_dict   = gc_dict,   \
                                ac_dict   = ac_dict,   \
                                awc_dict  = awc_dict,  \
                                other_rev = other_rev, \
                                stage     = stage,     \
                                form      = form)

#--------------------------------------------------------------------------
#-- get_data: for a given <obsid>.<rev> extract all needed data          --
#--------------------------------------------------------------------------

def get_data(name):
    """
    for a given <obsid>.<rev> extract all needed data
    input:  name        --- <obsid>.<rev>
    output: d_dict      --- dict of param <---> param values 
                            (org, req, current, and status ind)
            p_list      --- a list of parameters
            gc_dict     --- dict of general parameter changes
            ac_dict     --- dict of acis parameter changes
            awc_dict    --- dict of acis window parameter changes
            other_rev   --- other revisions available 
    """
#
#--- check whether the data file exists
#
    name      = os.path.join(current_app.config['OCAT_DIR'],'updates',name)

    if not os.path.isfile(name):
        return False
#
#--- separate obsid and rev #
#
    atemp     = re.split('\/', name)
    btemp     = re.split('\.', atemp[-1])
    obsid     = btemp[0]
    rev       = btemp[1]
#
#--- check whether other revisions available 
#
    other_rev = ocf.find_other_revisions(obsid, rev)
#
#--- read the current database values
#
    ct_dict  = rod.read_ocat_data(obsid)
#
#--- initialize dict etc
#
    p_comment = ''                  #--- keep the past comment
    n_comment = ''                  #--- keep the updated comment
    p_remarks = ''                  #--- keep the past remarks
    n_remarks = ''                  #--- keep the updated remarks
    gc_dict   = {}                  #--- keep general parameter changes
    ac_dict   = {}                  #--- keep acis parameter changes
    awc_dict  = {}                  #--- keep acis window parameter changes
    d_dict    = {}                  #--- dict of param <---> [org val, req val]
    p_list    = []                  #--- a list of parameters
    chk       = 0
    pchk      = 0
#
#--- read the data file and go through each line to find information needed
#
    data = ocf.read_data_file(name)
    for ent in data:
        if ent.strip() == '':
            continue

        if chk == 0:
#
#--- skipping the header parameter part
#
            if pchk == 0:
#
#--- reading submission status
#
                mc   = re.search('VERIFIED', ent)
                if mc is not None:
                    atemp = re.split('AS', ent)
                    val   = atemp[1].strip()
                    if val == 'IS':
                        val = 'ASIS'
                    d_dict['ASIS'] = [val, val, val]

                pchk = line_change_check(ent, pchk)
                continue
#
#--- read past comments
#
            elif pchk == 1:
                pchk = line_change_check(ent, pchk)
                if pchk > 1:
                    continue

                p_comment = p_comment + ' ' + ent
                continue
#
#--- read new comments 
#
            elif pchk == 2:
                pchk = line_change_check(ent, pchk)
                if pchk > 2:
                    continue

                n_comment = n_comment + ' ' + ent
                continue
#
#--- read past remarks
#
            elif pchk == 3:
                pchk = line_change_check(ent, pchk)
                if pchk > 3:
                    continue

                p_remarks = p_remarks + ' ' + ent
                continue
#
#--- read new remarks
#
            elif pchk == 4:
                pchk = line_change_check(ent, pchk)
                if pchk > 4:
                    continue

                n_remarks = n_remarks + ' ' + ent
                continue
#
#--- create dict of general changes
#
            elif pchk == 5:
                pchk = line_change_check(ent, pchk)
                if pchk > 5:
                    continue
#
#--- older time constraint time format is different
#--- convert it into a new format
#
                mc1 = re.search('TSTART', ent)
                mc2 = re.search('TSTOP',  ent)
                if mc1 is not None or mc2 is not None:
                    ent = adjust_time_order_in_general(ent)

                out = read_org_req_values(ent)
                gc_dict[out[0]] = out[1]
#
#--- create dict of acis param changes
#
            elif pchk == 6:
                pchk = line_change_check(ent, pchk)
                if pchk > 6:
                    continue

                out = read_org_req_values(ent)
                ac_dict[out[0]] = out[1]
#
#--- create dict of acis window param changes
#    
            elif pchk == 7:
                pchk = line_change_check(ent, pchk)
                if pchk > 7:
                    continue

                out = read_org_req_values(ent)
                awc_dict[out[0]] = out[1]
#
#--- skipping comment/table header lines
#
            mc = re.search('PARAM', ent)
            if mc is not None:
                chk = 1
                continue
            else:
                continue
        elif chk == 1:
            mc = re.search('-', ent)
            if mc is not None:
                chk = 2
        elif chk > 1:
#
#--- start reading parameter table part
#--- parameter name is between 0 and 27; older format is different
#
            param = ent[0:27]
#
#--- skip an empty line and a divider line
#
            if param == '':
                continue
            mc    = re.search('----', param)
            if mc is not None:
                continue
#
#--- original value is located between 27 and 54
#
            org   = ent[27:54]
#
#--- requested value is located after 54
#
            req   = ent[54:]
#
#--- create a dict and a list of parameter names
#
            param = param.strip()
            out   = org.strip()
            org   = check_neumeric_value(out)
            out   = req.strip()
            req   = check_neumeric_value(out)
#
#--- add the current db values (ranked case first)
#
            if ocf.is_neumeric(param[-1]) or param.lower() in ordr_list:
                d_dict = order_cases(param, d_dict, org, req, ct_dict)
                if param[-1] == '1':
                    p_list.append(str(param[:-1]))
            else:
                try:
                    crt   = ct_dict[param.lower()]
                except: 
                    crt   = 'NA'
                d_dict[param] = [org, req, crt]
                p_list.append(param)
#
#--- if new comment/remarks section is emptry, it means that the content did not change
#--- just copy from the past remarks/comment
#
    if n_remarks == '':
        n_remarks = p_remarks
    if n_comment == '':
        n_comment = p_comment
#
#--- adjust old time format in time constraint seciton
#
    d_dict = adjust_time_order_format(d_dict, 'TSTART')
    d_dict = adjust_time_order_format(d_dict, 'TSTOP')
#
#--- add status indicators to the parameter value dictionary
#
    d_dict = add_status_indicator(d_dict, p_list)
#
#--- add some info to dict before start reading the data file
#
    dname = str(obsid) + '.' + str(rev)
    d_dict['OBSREV'] = [dname, dname, dname, 0]
#
#-- find the file creation date
#
    out   = time.ctime(os.path.getmtime(name))
    atemp = re.split('\s+', out)
    cdate = atemp[1] + ' ' + ocf.add_leading_zero(atemp[2], 2) + ' ' + atemp[-1]
    d_dict['CDATE'] = [cdate, cdate, cdate, 0]
#
#--- add missing parameters
#
    d_dict = add_extra_values_to_dict(d_dict, ct_dict)

#
#--- Correct d_dict if changed parameters are not listed in the "full listing" of obscat parameters in revision file.
#
    #TODO Create handling for the awc_dict parameters.
    for key in gc_dict.keys():
        if key in d_dict.keys():
            d_dict[key][0] = gc_dict[key][0]
            d_dict[key][1] = gc_dict[key][1]

    for key in ac_dict.keys():
        if key in d_dict.keys():
            d_dict[key][0] = ac_dict[key][0]
            d_dict[key][1] = ac_dict[key][1]


#
#-- update remarks and comment dict entry
#
    d_dict = check_reamrks_and_comments('REMARKS',  p_remarks, n_remarks, d_dict)
    d_dict = check_reamrks_and_comments('COMMENTS', p_comment, n_comment, d_dict)

    return [d_dict, p_list, gc_dict, ac_dict, awc_dict, other_rev]

#--------------------------------------------------------------------------
#-- line_change_check: check data group change                           --
#--------------------------------------------------------------------------

def line_change_check(ent, pchk):
    """
    check data group change
    input:  ent     --- a data line
            pchk    --- a current group id
    output: pchk    --- a updated group id
    """
#
#--- change of the group is detected by the group header
#
    mc1 = re.search('PAST COMMENTS',   ent)
    mc2 = re.search('NEW COMMENTS',    ent)
    mc3 = re.search('PAST REMARKS',    ent)
    mc4 = re.search('NEW REMARKS',     ent)
    mc5 = re.search('GENERAL CHANGES', ent)
    mc6 = re.search('ACIS CHANGES',    ent)
    mc7 = re.search('ACIS WINDOW',     ent)
    mc8 = re.search('-----',           ent)

    if mc1 is not None:
        pchk = 1

    elif mc2 is not None:
        pchk = 2

    elif mc3 is not None:
        pchk = 3

    elif mc4 is not None:
        pchk = 4

    elif mc5 is not None:
        pchk = 5

    elif mc6 is not None:
        pchk = 6

    elif mc7 is not None:
        pchk = 7

    elif mc8 is not None:
        pchk = 8

    return pchk

#--------------------------------------------------------------------------
#-- read_org_req_values: read a line of <param name> changed from <org val> to <new val>
#--------------------------------------------------------------------------

def read_org_req_values(ent):
    """
    read a line of <param name> changed from <org val> to <new val>
    input:  ent             --- a line of data
    output: pname           --- a parameter name
            [oval, rval]    --- a list of original value and requested value
    """
    out = ['NA', ['', '']]
#
#--- just in a case an empty line came in
#
    if ent.strip() == '':
        return out

    try:
        atemp = re.split('changed from', ent)
        pname = atemp[0].strip()
        btemp = re.split('to' , atemp[1])

        out   = btemp[0].strip()
        oval  = check_neumeric_value(out)
        out   = btemp[1].strip()
        rval  = check_neumeric_value(out)

        return [pname, [oval, rval]]
    except:
        return out

#--------------------------------------------------------------------------
#-- check_neumeric_value: check whether value is a numeric, and if so return float or int value
#--------------------------------------------------------------------------

def check_neumeric_value(ent):
    """
    check whether value is a numeric, and if so return float or int value
    input:  ent --- value to be chcked  
    output: if it is float, float value is returned, if it is int, int value
            is return, otherwise the original value is returned
    """
    if ocf.is_neumeric(ent):
        val  = float(ent)
        ival = int(val)
        if val == ival:
            return ival
        else:
            return val
    else:
        return ent

#--------------------------------------------------------------------------
#-- add_status_indicator: add  status indicator to dictionary
#--------------------------------------------------------------------------

def add_status_indicator(d_dict, p_list):
    """
    add  status indicator to dictionary
    input:  d_dict  --- dict of <param name> <--> [<org value>, <req value>]
            p_list  --- a list of parameters
    output: d_dict  --- dict of<param name> 
                        <-->[<org value>, <req value>, <db value>, <status ind> ]
                            ind = 0 if org value == req value == db value
                            ind = 1 if org value != req value but req value == db value
                            ind = 2 if no req value (''), but org value != db value
                            ind = 3 if req value != db value
    """
#
#--- find the current database values for all parameter values
#--- org: original value / req: requested value / crt: the current value in the database
#
    for ent in d_dict.keys():
        try:
            [org, req, crt] = d_dict[ent]
        except:
            org = ''
            req = ''
            crt = ''
#
#--- check status and set indicator
#
#--- first ranked case which has more than one possible entries
#
        if type(org) == list:
            i_list = []
            for k in range(0, 10):
                oval = org[k]
                nval = req[k]
                cval = crt[k]
                ind  = set_color_indicator(oval, nval, cval)
                i_list.append(ind)

            d_dict[ent] = [org, req, crt, i_list]
#
#--- for the normal single entry case
#
        else:
            ind         = set_color_indicator(org, req, crt)
            d_dict[ent] = [org, req, crt, ind]

    return d_dict

#--------------------------------------------------------------------------
#-- set_color_indicator: set color indicator depending of data status    --
#--------------------------------------------------------------------------

def set_color_indicator(org, req, db_val):
    """
    set color indicator depending of data status
    input:  org     --- original value
            req     --- requested value
            db_val  --- database value
    output: ind     --- 0 if org value == req value == db value
                        1 if org value != req value but req value == db value
                        2 if no req value (''), but org value != db value
                        3 if req value != db value
    """
#
#--- if the value is nuemric, round up to a 4-decimal float value
#
    if ocf.is_neumeric(db_val) or ocf.is_neumeric(org) or ocf.is_neumeric(req):
        if ocf.is_neumeric(org):
            org    = float('%3.4f' % round(float(org),4))
        else:   
            org    = org.strip()

        if ocf.is_neumeric(req):
            req    = float('%3.4f' % round(float(req),4))
        else:  
            req    = req.strip()

        if ocf.is_neumeric(db_val):
            db_val = float('%3.4f' % round(float(db_val),4))
        else:  
            db_val = str(db_val).strip()

        ind = 0
#
#--- if the value is not neumeric, remove leading and tailing white spance
#
    else:
        org    = org.strip().replace(' ', '')
        req    = req.strip().replace(' ', '')
        db_val = str(db_val).strip().replace(' ', '')
        ind    = 0
#
#--- handling special cases
#
        cind = check_null_case(org, req, db_val)
        if cind >= 0:
            return cind
#
#--- handling 'default' case
#
        """
        cind = check_default_case(org, req, db_val)
        if cind >= 0:
            return cind 
        """
#
#--- if org value and req value are same
#
    if org == req:
        if org != db_val:
            ind = 2
#
#--- if org value and req value are different
#
    else:
        if req == db_val:           #--- req value and db value agree
            ind = 1
        if req in null_list:        #--- no new req value
            if org != db_val:       #--- but if org value is different from db value
                ind = 2
            else:
                ind = 3
        else:
            if req != db_val:       #--- req value exists and different from db value
                ind = 3

    return ind

#--------------------------------------------------------------------------
#-- check_null_case: check requested value and database vlue are null    --
#--------------------------------------------------------------------------

def check_null_case(org, req, db_val):
    """
    check requested value and database vlue are null
    input:  org     --- original value (not used)
            req     --- requested value
            dv_val  --- database value
    output:  0      --- if they are null values
            -1      --- they are not null values
    """
    if db_val in null_list:
        if req in null_list:
            if org in null_list:
                return 0

    return -1

#--------------------------------------------------------------------------
#-- check_default_case: check whther reqested value and database values are default 
#--------------------------------------------------------------------------

def check_default_case(org, req, db_val):
    """
    check whther reqested value and database values are default
    input:  org     --- original value (not used)
            req     --- requested value
            dv_val  --- database value
    output:  0      --- if all of them are default/null
             1      --- reqested and db value are default/null
            -1      --- they are not null nor default
    """
    org_t = org.lower().strip()
    req_t = req.lower().strip()
    db_t  = db_val.lower().strip()

    if db_t == 'default' or db_t in null_list:
        if req_t == 'default' or req_t in null_list:
            if org_t == 'default' or req_t in null_list:
                return 0
            else:
                return 1
    return -1

#--------------------------------------------------------------------------
#-- add_extra_values_to_dict: add missing data into the dictionary       --
#--------------------------------------------------------------------------

def add_extra_values_to_dict(d_dict, ct_dict):
    """
    add missing data into the dictionary 
    input:  d_dict  --- current dictionary 
            ct_dict --- a dictionary which lists all parameters from the database
    output: d_dict  --- a dictionary which is added missing parameters from ct_dict
    """
    tmp = ['NA'] * 10
    for ent in all_param_list:
#
#--- check whether the data are already in the dict
#
        try:
            out = d_dict[ent]
#
#--- if not, check database value
#
        except:
            try:
                out = ct_dict[ent.lower()]
            except:
                out = ''
#
#--- check whether the database value is a list; if so, org and req should be lists, too
# 
            if type(out) == list:
                d_dict[ent] = [tmp,  tmp,  out, 0]
            else:
                d_dict[ent] = ['NA', 'NA', out, 0]
#
#--- add acis window order as 'aw_ordr'
#--- in the older system ordr is the counter, but in the newer
#--- system, we use chip
#
    out = d_dict['ORDR']
    if isinstance(out, list):
        for k in range(0, 10):
            if isinstance(out[1], list):
                if out[1][k] in null_list:
                    break
            else:
                break
    if k == 0:
        out = d_dict['CHIP']
        for k in range(0, 10):
            if out[1][k] in null_list and out[2][k] in null_list:
                break

    aw_ordr = k + 1
    d_dict['AW_ORDR'] = [k, k, k, 0]

    return d_dict

#--------------------------------------------------------------------------
#-- check_reamrks_and_comments: compare the text based entries to see whether they are the same
#--------------------------------------------------------------------------

def check_reamrks_and_comments(name, o_line, r_line, d_dict):
    """
    compare the text based entries to see whether they are the same
    input:  name    --- parameter name
            o_line  --- original text
            r_line  --- requested text
            d_dict  --- data dictonary
    output: d_dict  --- data dictionary with the text based entry with status indicator
    """
#
#--- remove all white spaces from the texts
#
    d_line  = d_dict[name][2]
    so_line = ''.join(o_line.split()).lower()
    sr_line = ''.join(r_line.split()).lower()
    sd_line = ''.join(d_line.split()).lower()
#
#--- compare three texts to determine status indicator
#
    ind = 0
    if so_line == sr_line:
        if so_line != sd_line:
            ind = 2
    else:
        if sr_line == '':
            if so_line != sd_line:
                ind = 2
        else:
            if sr_line != sd_line:
                ind = 3
#
#--- put the result back in the dict
#
    d_dict[name] = [o_line, r_line, d_line, ind]

    return d_dict

#--------------------------------------------------------------------------
#-- order_cases: update dictonary for ordered case                       --
#--------------------------------------------------------------------------

def order_cases(param, d_dict, oval, nval, cv_dict):
    """
    update dictonary for ordered case such as window constraints/roll constraints/acis window
    input:  prama   --- name of parameter in the form of <name><rank> where rank start from 1
            d_dict  --- data dictionary
            oval    --- original value of the parameter of that rank
            nval    --- requested value of the parameter of that rank
            cv_dict --- a dictionary of current parameter <--> value in the database
    ouput:  d_dict  --- updated data dictionary
    """
    tmp  = ['NA', 'NA','NA','NA','NA','NA','NA','NA','NA','NA']
    tmp1 = copy.deepcopy(tmp)
    tmp2 = copy.deepcopy(tmp)
    tmp3 = copy.deepcopy(tmp)
#
#--- parameter name is the form of <name><rank> (e.g., TSTART1); separate it to name and rank value
#
    if ocf.is_neumeric(param[-1]):
        name = param[:-1]
        rank = int(float(param[-1]))
    else:
        name = param
        rank = 1
#
#--- check whether the dict already has the entry for this param
#--- if not, set up an list of empty lists for original values/requested values
#
    if name in d_dict.keys():
        out = d_dict[name]
    else:
        out = [tmp1, tmp2, tmp3]
#
#--- rank starts from 1; position starts from 0
# 
    pos  = rank - 1
    out[0][pos] = oval
    out[1][pos] = nval
#
#--- current database entries
#
    lname = name.lower()
    if lname in cv_dict.keys():
        np = cv_dict[lname]
    else:
        np = tmp3

    d_dict[name] = [out[0], out[1], np]

    return d_dict
    
#--------------------------------------------------------------------------
#-- adjust_time_order_in_general:converting the older time display format into a new one
#--------------------------------------------------------------------------

def adjust_time_order_in_general(line):
    """
    converting the older time display format into a new one in the Change Requested section
    input:  line    --- a data line
                ex: time_ordr= 1: TSTART changed from 03:09:2022:00:00:00 to 03:09:2023:00:00:00
    output: line    --- an updated data line
    """
    atemp = re.split('from ', line)
    btemp = re.split('to', atemp[1])
    try:
        torg  = btemp[0].strip()
    except:
        torg  = 'NA'
    try:
        tnew  = btemp[1].strip()
    except:
        tnew  = 'NA'

    if torg in null_list or torg == '':
        torg = 'NA'

    if tnew in null_list or tnew == '':
        tnew = 'NA'

    norg = check_formt_change(torg)
    nnew = check_formt_change(tnew)

    line = atemp[0] + 'from ' + norg + ' to ' + nnew

    return line
    
#--------------------------------------------------------------------------
#-- adjust_time_order_format: converting the older time display fromat into a new one
#--------------------------------------------------------------------------

def adjust_time_order_format(d_dict, tparam):
    """
    converting the older time display fromat into a new one in the table section
    d_dict  --- a dict of data
    tparam  --- TSTART or TSTOP
    d_dict  --- an updated dict of data
    """
    if tparam in d_dict.keys():
        out    = d_dict[tparam]
        osave  = []
        nsave  = []
        for k in range(0, 10):
            osave.append(check_formt_change(out[0][k]))
            nsave.append(check_formt_change(out[1][k]))
    
        out[0] = osave
        out[1] = nsave
    
        d_dict[tparam] = out

    return d_dict

#--------------------------------------------------------------------------
#-- check_formt_change: convert time fromat to <YYY>-<mm>-<dd>T<HH>:<MM>:<SS>
#--------------------------------------------------------------------------

def check_formt_change(tval):
    """
    convert time fromat: <mm>:<dd>:<yyy>:<hh>:<mm>:<ss> to <YYY>-<mm>-<dd>T<HH>:<MM>:<SS>
    input:  time value
    output: time in <YYY>-<mm>-<dd>T<HH>:<MM>:<SS>; if conversion fails, original value
    """
    if tval in null_list:
        return tval

    mc = re.search('T', str(tval))
    if mc is None:
        try:
            atemp = re.split(':', tval)
            alen  = len(atemp)
            for k in range(alen, 6):
                tval = tval + ':00'
            tval = tval.replace('::', ':')
            tval = time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(tval, '%m:%d:%Y:%H:%M:%S'))
        except:
            pass

    return tval






