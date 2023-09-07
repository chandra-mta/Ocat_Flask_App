#################################################################################
#                                                                               #
#       ocat data page                                                          #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                               #
#           last update: Oct 21, 2021                                           #
#                                                                               #
#################################################################################
import os
import sys
import re
import string
import time
import Chandra.Time
import copy
from   datetime         import datetime
import numpy

from flask              import render_template, flash, redirect, url_for
from flask              import session, request, current_app, escape
from flask_login        import current_user

from app                import db
from app.models         import User, register_user 
from app.ocatdatapage   import bp
from app.ocatdatapage.forms import OcatParamForm

import app.supple.ocat_common_functions         as ocf
import app.supple.read_ocat_data                as rod
import app.ocatdatapage.create_selection_dict   as csd
import app.ocatdatapage.check_value_range       as cvr
import app.ocatdatapage.update_data_record_file as udrf
import app.ocatdatapage.submit_other_obsids     as soo
import app.ocatdatapage.send_notifications      as snt
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
#--- read ocat parameter list
#
basedir = os.path.abspath(os.path.dirname(__file__))
p_file  = os.path.join(basedir, '../static/param_list')
with open(p_file, 'r') as f:
    all_param_list = [line.strip() for line in f.readlines()]
#
#--- define several data lists
#
null_list = [None, 'NA',  'NULL', 'None', 'NONE',   'null', 'none', '', ' ']
na_list   = ['NA', 'NA','NA','NA','NA','NA','NA','NA','NA','NA']

time_list = ['window_constraint', 'tstart', 'tstop', \
              'tstart_month', 'tstart_date', 'tstart_year', 'tstart_time',\
              'tstop_month',  'tstop_date',  'tstop_year',  'tstop_time',]

tsht_list = ['tstart', 'tstop', 'window_constraint']

roll_list = ['roll_constraint', 'roll_180', 'roll', 'roll_tolerance',]

awin_list = ['chip', 'start_row', 'start_column',\
              'height', 'width', 'lower_threshold', 'pha_range', 'sample',] 

rank_list = time_list + roll_list + awin_list

nshw_list = ['monitor_series','remarks', 'comments', 'approved',\
             'group_obsid', 'dec', 'ra', 'acis_open', 'hrc_open']

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
#-- index: this is the main function to display ocatdata page            --
#--------------------------------------------------------------------------

@bp.route('/',              methods=['GET', 'POST'])
@bp.route('/<obsid>',       methods=['GET', 'POST'])
@bp.route('/index/<obsid>', methods=['GET', 'POST'])
def index(obsid=''):

    form     = OcatParamForm()
#
#--- check an obsid given is in a proper form
#
    if (not obsid in ['', None]) and ocf.is_integer(obsid):
#
#--- read the current database values
#
        try:
            ct_dict  = csd.create_selection_dict(obsid)
        except Exception as create_selection_dict_exc: #use variable e for debugging purposes beyond failure to find Obsid in the database.
            session.pop('_flashes', None)
            flash('Obsid is not found in the database!')

            return render_template('ocatdatapage/provide_obsid.html', form=form)
#
#--- check observation status and, if needed, create a warning header for the page
#
        warning  = csd.create_warning_line(obsid)
#
#--- if data are submitted from the main page, update the data dictionary
#
        if 'submit_test' in request.form:
            ct_dict, obsids_list = update_ct_dict(ct_dict, request.form)
#
#--- if Refresh button was pushed, usually rank related update
#
            if 'check' in request.form:
                ct_dict = update_values(request.form, ct_dict)
#
#--- if Submit button was pushed, submit changes to the next step
#
            if 'submit' in request.form:
                asis, wnote, disp_param_list, obsids_disp, ct_dict, ind_dict, or_dict\
                                         = process_submit_data(ct_dict, request.form)

                return render_template('ocatdatapage/display_parameters.html',\
                                            ct_dict         = ct_dict,
                                            ind_dict        = ind_dict,
                                            disp_param_list = disp_param_list,
                                            time_list       = tsht_list,
                                            time_all_list   = time_list,
                                            roll_list       = roll_list,
                                            awin_list       = awin_list,
                                            asis            = asis, 
                                            wnote           = wnote,
                                            obsids_disp     = obsids_disp,
                                            or_dict         = or_dict,
                                            form            = form)
#
#--- returning to the main page from the parameter check page
#
        elif 'return'   in request.form:
            ct_dict     = restore_parameters(ct_dict, request.form)
#
#--- finalize
#
        elif 'finalize' in request.form:
            asis, ct_dict, notes, ostatus, sobsids_list, not_processed, no_change\
                    = process_data_for_finalize(ct_dict, request.form)

            return render_template('ocatdatapage/finalize.html',\
                            obsid       = ct_dict['obsid'][-1],
                            asis        = asis,
                            status      = ct_dict['status'][-1],
                            obsids_disp = sobsids_list,
                            no_process  = not_processed,
                            no_change   = no_change,
                            form        = form)
#
#--- main page display
#
        return render_template('ocatdatapage/index.html',\
                            ct_dict = ct_dict,
                            warning = warning,
                            form    = form)
#
#--- if the obsid is not provided, this page will open
#
    else:
        return render_template('ocatdatapage/provide_obsid.html',\
                                form = form)

#--------------------------------------------------------------------------
#-- update_ct_dict: update data disctionry with submitted values         --
#--------------------------------------------------------------------------

def update_ct_dict(ct_dict, f_data):
    """
    update data disctionry with submitted values
    input:  ct_dict     --- the data dictionary
            f_data      --- form data
    output: ct_dict     --- updated data dictionary
            obsids_list --- a list of obsids which will be updated with
                            the same parameter chages
    """
#
#--- compare the keys in the data dictionary and those in the form data
#--- and update the dictonary value 
#
    for key in ct_dict.keys():
        if key in f_data:
            val          = f_data[key]
            val          = ocf.is_integer(val)  #--- string to interger
            out          = ct_dict[key]
            out[-1]      = val
            ct_dict[key] = out
#
#--- update those with display values are different from those of the database values
#
    ct_dict = radec_convertion(ct_dict)
    ct_dict = dither_convertion(ct_dict)
#
#--- if the instrument is hrc, the general si mode is same as hrc si mode
#
    if ct_dict['instrument'][-1] in ['HRC-I', 'HRC-S']:
            ct_dict['si_mode'][-1] = ct_dict['hrc_si_mode'][-1]
#
#--- ranked entries are handled slighly differently
#
    ct_dict = update_rank_values_from_f_data(f_data, ct_dict)
#
#--- check request for opening editing window the first time for a specific section
#
    if 'dither_edit' in f_data:
        ct_dict['dither_flag'][-1]          = 'Y'

    if 'window_edit' in f_data:
        ct_dict['window_flag'][-1]          = 'Y'
        ct_dict['time_ordr'][-1]            =  1
        ct_dict['window_constraint'][-1][0] = 'Y'

    if 'roll_edit' in f_data:
        ct_dict['roll_flag'][-1]            = 'Y'
        ct_dict['roll_ordr'][-1]            =  1
        ct_dict['roll_constraint'][-1][0]   = 'Y'

    if 'awin_edit' in f_data:
        ct_dict['spwindow_flag'][-1]        = 'Y'
        ct_dict['aciswin_no'][-1]           =  1
        ct_dict['chip'][-1][0]              = 'I0'

    if 'obsids_list' in f_data:
        obsids_list                         = f_data['obsids_list']
    else:
        obsids_list = []

    return ct_dict, obsids_list

#--------------------------------------------------------------------------
#-- process_submit_data: prepare to display parameter values on the parameter display page
#--------------------------------------------------------------------------

def process_submit_data(ct_dict, f_data):
    """
    prepare to display parameter values on the parameter display page
    input:  ct_dict     --- a dict of data
            f_data      --- form data
    output: asis        --- asis status
            wnote       --- warning note, such as whether obsid is on OR list
            dis_param_list  --- a list of parameter names which will be
                                displayed on the page
            obsids_disp     --- a list of obsids which will be update similarly
            ct_dict         --- an updated dict of data
            ind_dict        --- a dict of param <---> whether the value is update
            or_dict         --- a dict of obsids <---> OR list status
    """
    chk    = f_data['submit']
    if chk == 'Submit':
#
#--- if asis not given, assume it is 'norm'
#
        if 'asis' in f_data:
            asis     = f_data['asis']
        else:
            asis     = 'norm'
#
#--- update ra/dec in degee; tstart/stop in form of <yyyy>-<mm>-<dd>T<HH>:<MM>:<SS>
#--- if the instrument was changed from acis to hrc or another way around
#--- nullify the parameter values of the original instrument
#
        ct_dict  = radec_convertion(ct_dict)
        ct_dict  = update_tstart_tstop(ct_dict)
        ct_dict  = csd.nullify_entries(ct_dict)
#
#--- create a dict of <parameter> <---> <whether org and new parameter value matchs>
#---                1: if matches 0: if not

        ind_dict = csd.create_match_dict(ct_dict)
#
#--- params in remove_list won't show in the param display page table
#--- or handled differently (such as ranked paramters)
#
        disp_param_list = []
        remove_list    = rank_list + nshw_list 
        for ent in ct_dict.keys():
            if ent in remove_list:
                continue
            else:
                disp_param_list.append(ent)
#
#--- check whether the parameter values are in the expected range, if not,
#--- create warning texts for display on the parameter value display page
#
        wnote       = cvr.check_value_range(ct_dict)
#
#--- if multiple obsids are submitted, pass the list of the obsids
#
        obsids_disp = create_display_obsid_list(f_data, ct_dict['obsid'][-1])
#
#--- check whether any of obsids are in the active OR list
#
        or_dict     = check_obsid_in_or_list(obsids_disp)

    return asis, wnote, disp_param_list, obsids_disp, ct_dict, ind_dict, or_dict
    
#--------------------------------------------------------------------------
#-- process_data_for_finalize: prepare for the finail page and update the databases
#--------------------------------------------------------------------------

def process_data_for_finalize(ct_dict, f_data):
    """
    prepare for the finail page and update the databases
    input:  ct_dict         --- a dict of data
            f_data          --- a form data
    output: acis            --- asis status
            ct_dict         --- an updated ddata dict
            notes           --- notes from multiple submissions: 3types of note in order
                                of obsid in obsids_list
                                [[<coordindate shift>], [sch date <10days?>], [OR list?]]
            ostatus         --- status of obsids on the multiple submission list
            sobsid_list     --- a list of obsids successfully update
            not_processed   --- a list of obsids which were not udpated
            <data_dir>/updates/<obsid>.<rev#>
            <data_dir>/updates_table.list
            <data_dir>/approved (if asis == 'asis'/'remove')
    """
    ct_dict     = restore_parameters(ct_dict, f_data)
    ind_dict    = csd.create_match_dict(ct_dict)
    user        = current_user.username
    obsid       = ct_dict['obsid'][-1]
    obsids_disp = create_display_obsid_list(f_data, obsid)

    if 'asis' in f_data:
        asis = f_data['asis']
    else:
        asis = 'norm'
#
#--- if asis is not norm, we don't want to report any parameter changes; so put back the 
#--- original data. for clone case, the comments section needs to be updated
#
    if asis != 'norm':
        if asis == 'clone':
            save = ct_dict['comments'][-1]

        ct_dict  = csd.create_selection_dict(obsid)

        if asis == 'clone':
            ct_dict['comments'][-1] = save
#
#--- create a data recrod file in <data_dir>
#--- changed_param is a text to list updated parameter values
#--- note is a list of lists to pass information about mp/arcorp/hrc notifications
#
    changed_param, note = udrf.update_data_record_file(ct_dict, ind_dict, asis, user)
#
#--- if multiple obsid updates are requested, update all
#
    no_change = []
    if len(obsids_disp) > 0:
        notes, ostatus, no_change = soo.submit_other_obsids(obsids_disp, ct_dict, ind_dict, asis, user)
#
#--- combine notes to mp;
#
        for k in range(0, 3):
            note[k] = note[k] + notes[k]
    else:
        notes   = [[],[],[]]
        ostatus = []
#
#--- send email to only "active" obsids
#
    sobsids_list  = []
    not_processed = []
    if len(obsids_disp) > 0:
        for k in range(0, len(obsids_disp)):
            if ostatus[k] in ['scheduled', 'unobserved']:
                sobsids_list.append(str(obsids_disp[k]))
            else:
                not_processed.append(str(obsids_disp[k]))
#
#--- 
    if len(no_change) > 0:
        d_list = numpy.setdiff1d(sobsids_list, no_change)
    else:
        d_list = sobsids_list
#
#--- send notifications
#
    if len(sobsids_list) > 0:
        snt.send_notifications(asis, ct_dict, d_list, changed_param, note)

    return asis, ct_dict, notes, ostatus, d_list, not_processed, no_change

#--------------------------------------------------------------------------
#-- update_rank_values_from_f_data: update ranked entries of ct_dict     --
#--------------------------------------------------------------------------

def update_rank_values_from_f_data(form, ct_dict):
    """
    update ranked entries of ct_dict
    input:  form    --- form data 
            ct_dict --- a dict of p_id <---> <data information>
    output: ct_dict --- updated dict
    """
#
#--- time constraints
#
    ct_dict = rank_val_loop(form, ct_dict, time_list)
    chk     = rank_null_cnt(ct_dict, 'window_constraint')
    if chk == 0:
        ct_dict['window_flag'][-1]   = 'N'
    ct_dict['time_ordr'][-1]         = chk
#
#--- roll constraints
#
    ct_dict = rank_val_loop(form, ct_dict, roll_list)
    chk     = rank_null_cnt(ct_dict, 'roll_constraint')
    if chk == 0:
        ct_dict['roll_flag'][-1]     = 'N'
    ct_dict['roll_ordr'][-1]         = chk
#
#--- acis window 
#
    ct_dict = rank_val_loop(form, ct_dict, awin_list)
    chk     = rank_null_cnt(ct_dict, 'chip')
    if chk == 0:
        ct_dict['spwindow_flag'][-1] = 'N'
        ct_dict['acis_open'][-1]     = 'close'
    ct_dict['aciswin_no'][-1]        = chk

    return ct_dict

#--------------------------------------------------------------------------
#-- rank_val_loop: update ranked parameter values for a given ranked group 
#--------------------------------------------------------------------------

def rank_val_loop(form, ct_dict, d_list):
    """
    update ranked parameter values for a given ranked group
    input:  form    --- form data
            ct_dict --- a dict of <parameter> <---> <informaiton>
            d_list  --- a list of parameters in the group
    output: ct_dict --- an updated data dict
    """
    for param in d_list:
        save = []
        for k in range(0, 10):
            name = param +  '_' + str(k)
            if name in form:
                val  = form[name]
                if val == '':
                    chk = ct_dict[param][-1][k]
                    if chk in null_list:
                        val = chk
                save.append(val)
            else:
                save.append('NA')

        if len(save) > 0:
            out            = ct_dict[param]
            out[-1]        = save
            ct_dict[param] = out
                
    return ct_dict

#--------------------------------------------------------------------------
#-- rank_null_cnt: count numbers of non_null entries in the ranked parameters 
#--------------------------------------------------------------------------

def rank_null_cnt(ct_dict, nparam):
    """
    count numbers of non_null entries in the ranked parameters
    input:  ct_dict --- a data dict of <param> <--> <information>
            nparam  --- parameter name
    ouput:  chk     --- the numbers of the non_null entries
    """
    chk = 0
    for ent in ct_dict[nparam][-1]:
        if not ent in null_list:
            chk += 1

    return chk

#--------------------------------------------------------------------------
#-- update_values: update rank related entries                           --
#--------------------------------------------------------------------------

def update_values(form, ct_dict):
    """
    update rank related entries
    input:  form    --- form values
            ct_dict --- a dict of <param> <---> <info>
    output: ct_dict --- an updated dict
    """
    chk = form['check']
#
#--- opening rank entries
#
    if chk == 'Refresh':
        if ct_dict['window_flag'][-1] == 'Y':
            if ct_dict['time_ordr'][-1] == 0:
                ct_dict['time_ordr'][-1] = 1

        if ct_dict['roll_flag'][-1] == 'Y':
            if ct_dict['roll_ordr'][-1] == 0:
                ct_dict['roll_ordr'][-1] = 1

        if ct_dict['spwindow_flag'][-1] == 'Y':
            if ct_dict['aciswin_no'][-1] == 0:
                ct_dict['aciswin_no'][-1] = 1
#
#--- time rank case
#
    elif chk == 'Add Time Rank':
        ct_dict = add_rank('time_ordr', ct_dict, 'window_constraint', 'Y')

    elif chk == 'Remove NA Time Entry':
        p_param = 'window_constraint'
        r_param = 'time_ordr'
        flag    = 'window_flag'
        ct_dict = remove_null_rank(p_param, r_param, flag, time_list, ct_dict)
#
#--- roll rank case
#
    elif chk == 'Add Roll Rank':
        ct_dict = add_rank('roll_ordr', ct_dict, 'roll_constraint', 'Y')

    elif chk == 'Remove NA Roll Entry':
        p_param = 'roll_constraint'
        r_param = 'roll_ordr'
        flag    = 'roll_flag'
        ct_dict = remove_null_rank(p_param, r_param, flag, roll_list, ct_dict)
#
#--- acis window rank case
#
    elif chk == 'Add Window Rank':
        ct_dict = add_rank('aciswin_no', ct_dict, 'chip', 'I0')

    elif chk == 'Remove NA Window Rank':
        p_param = 'chip'
        r_param = 'aciswin_no'
        flag    = 'spwindow_flag'
        ct_dict = remove_null_rank(p_param, r_param, flag, awin_list, ct_dict)

    return ct_dict

#--------------------------------------------------------------------------
#-- restore_parameters: restore ct_dict "new" data set after passing though POST 
#--------------------------------------------------------------------------

def restore_parameters(ct_dict, form):
    """
    restore ct_dict "new" data set after passing though POST 
    input:  ct_dict --- a dict of <param> <--> <information>
            form    --- a data form
    output: ct_dict --- an updated data dict
    """
    for param in ct_dict.keys():

        if param in form:
            if param in ['monitor_series', 'group_obsid']:
                ct_dict[param][-1] = ct_dict[param][-2]
            else:
#
#--- if the value is float or int, convert that into float or int
#
                val = ocf.is_integer(form[param])
                ct_dict[param][-1] = val
#
#--- update ra/dec and dither amp/freq
#            
    ct_dict = radec_convertion(ct_dict)
    ct_dict = dither_convertion(ct_dict)
#
#--- ranked data passed differently; so handle them separately
#
    restore_rank_parameters(time_list, ct_dict, form, chk=1)
    restore_rank_parameters(roll_list, ct_dict, form)
    restore_rank_parameters(awin_list, ct_dict, form)

    return ct_dict

#--------------------------------------------------------------------------
#-- restore_rank_parameters: restore a list of data dict after passing through POST
#--------------------------------------------------------------------------

def restore_rank_parameters(a_list, ct_dict, form, chk=0):
    """
    restore a list of data dict after passing through POST
    input:  a_list  --- a list of ranked parameters
            ct_dict --- a dict of <parameter> <--> <information>
            form    --- a form data
            chk     --- if 0, convert neumeric value to float or int
                           1, keep string foramt even if it is neumeric value
    output: ct_dict --- an updated data dict
    """
#
#--- ranked data are passed from form in the form of <parameter name><rank>
#--- for example, tstart3 for tstart[3]
#
    for param in a_list:
        vlist = []
        for k in range(0, 10):
            pname = param + '_' + str(k)
            if pname in form:
                val = form[pname]
            else:
                val = ct_dict[param][-2][k]
#
#--- usually all nuemric values are changed into either integer or float, but
#--- some case, we want to keep in string
#
            if chk == 0:
                val = ocf.is_integer(val)
            
            vlist.append(val)
        ct_dict[param][-1] = vlist

    return ct_dict

#--------------------------------------------------------------------------
#-- add_rank: increase a rank by one                                     --
#--------------------------------------------------------------------------

def add_rank(param, ct_dict, pname, i_val):
    """
    increase a rank by one
    input:  param   --- a name of rank parameter
            ct_dict --- a dict of <param> <--> <information>
            pname   --- a name of paramter which indicates whether the row is open
            i_val   --- a value which the row is open (e.g. 'Y' for window_constraint)
    outpu;  ct_dict --- an updated dict 
    """
    val = ct_dict[param][-1] 
    if ocf.is_neumeric(val):
        val  = int(val)
        val += 1
        
    else:
        val  = 1
#
#--- change the rank of the ordered entiries
#
    ct_dict[param][-1]        = val
#
#--- indicate that the new row is open
#
    ct_dict[pname][-1][val-1] = i_val

    return ct_dict

#--------------------------------------------------------------------------
#-- remove_null_rank: remove a null rank entry                          ---
#--------------------------------------------------------------------------

def remove_null_rank(c_param, r_param, flag, p_list, ct_dict):
    """
    remove a null rank entry
    input:  c_param --- a parameter name which inidicates wheter the row is open
            r_param --- a rank  parameter name
            flag    --- a flag whether there is any ranks
            p_list  --- a list of ranked parameters
            ct_dict --- a dict of <param> <---> <information>
    output: ct_dict --- an updated dict
    """
#
#--- check all ranks and if the indicator says the row is closed
#--- change all other parameter values to 'NA'
#
    for k in range(0, 9):
        val1 = ct_dict[c_param][-1][k]
        if val1 in null_list:
            for name in p_list:
                ct_dict[name][-1][k] = 'NA'
#
#--- check how many ranks still have values
#
    pval = 0
    for k in range(0, 10):
        val = ct_dict[p_list[0]][-1][k]
        if val != 'NA':
            pval += 1

    ct_dict[r_param][-1] = pval
#
#--- if the all ranks are closed, change the flags to indicate that
#
    if pval == 0:
        ct_dict[r_param][-1] = 0 
        ct_dict[flag][-1]    = 'N'

    return ct_dict

#--------------------------------------------------------------------------
#-- update_tstart_tstop: update tstart and tstop from year/mon/date/time entries
#--------------------------------------------------------------------------

def update_tstart_tstop(ct_dict):
    """
    update tstart and tstop from year/mon/date/time entries
    input:  ct_dict --- a dict of <param> <--> <information>
    output: ct_dict --- an updated dict of <param> <--> <information>
    """ 
    start_out = ct_dict['tstart']
    stop_out  = ct_dict['tstop']
    for k in range(0, 10):
        start_year        = ct_dict['tstart_year'][-1][k]

        if start_year in null_list:
            continue

        start_month       = ct_dict['tstart_month'][-1][k]

        if not ocf.is_neumeric(start_month):
            start_month = ocf.change_month_format(start_month)

        start_date        = ct_dict['tstart_date'][-1][k]
        start_time        = ct_dict['tstart_time'][-1][k]
        start_time        = adjust_time_format(start_time)
        
    
        tstart            = start_year + '-' + ocf.add_leading_zero(start_month, 2) 
        tstart            = tstart     + '-' + ocf.add_leading_zero(start_date,  2)
        tstart            = tstart     + 'T' + start_time

        start_out[-1][k]  = tstart

        stop_year         = ct_dict['tstop_year'][-1][k]
        stop_month        = ct_dict['tstop_month'][-1][k]

        if not ocf.is_neumeric(stop_month):
            stop_month = ocf.change_month_format(stop_month)

        stop_date         = ct_dict['tstop_date'][-1][k]
        stop_time         = ct_dict['tstop_time'][-1][k]
        stop_time         = adjust_time_format(stop_time)
    
        tstop             = stop_year  + '-' + ocf.add_leading_zero(stop_month,  2) 
        tstop             = tstop      + '-' + ocf.add_leading_zero(stop_date,   2)
        tstop             = tstop      + 'T' + stop_time

        stop_out[-1][k]   = tstop 

    ct_dict['tstart']  = start_out
    ct_dict['tstop']   = stop_out

    return ct_dict

#--------------------------------------------------------------------------
#-- adjust_time_format: clearn up the format of time to <hh>:<mm>:<ss> format
#--------------------------------------------------------------------------

def adjust_time_format(ptime):
    """
    clearn up the format of time to <hh>:<mm>:<ss> format
    input:  ptime   --- time part of the data
    output: ptime   --- adjusted time
    """
#
#--- check the time is spaced with a white space
#
    mc     = re.search(':', ptime)
    if mc is None:
        ptime.strip()
        atemp = re.split('\s+', ptime)
        if len(atemp) > 1:
            ptime = ptime.replace('\s+', ':')
#
#--- check the time is propery formatted
#
    mc     = re.search(':', ptime)
    if mc is not None:
        atemp = re.split(':', ptime)
        if len(atemp) == 3:
            ptime = ocf.add_leading_zero(atemp[0], 2)  + ':'
            ptime = ptime +  ocf.add_leading_zero(atemp[1], 2)  + ':'
            ptime = ptime +  ocf.add_leading_zero(atemp[2], 2)
        elif len(atemp) == 2:
            ptime = ocf.add_leading_zero(atemp[0], 2)  + ':'
            ptime = ptime +  ocf.add_leading_zero(atemp[1], 2)  + ':00'
        elif len(atemp) == 1:
            ptime = ocf.add_leading_zero(atemp[0], 2)  + ':00:00'
        else:
            ptime = '00:00:00'
#
#--- time format does not comform; just give 00:00:00
#
    else:
        ptime = '00:00:00'

    return ptime

#--------------------------------------------------------------------------
#-- radec_convertion: update data dict ra dec values based on display ra dec values
#--------------------------------------------------------------------------

def radec_convertion(ct_dict):
    """
    update data dict ra dec values based on display ra dec values
    input:  ct_dict --- a dict of <param> <---> <information>
    output: ct_dict ---- a dict with ra/dec value updated
    """
    dra  = ct_dict['dra'][-1]
    ddec = ct_dict['ddec'][-1]

    ra, dec = ocf.convert_ra_dec_format(dra, ddec)

    ct_dict['ra'][-1]   = ra
    ct_dict['dec'][-1]  = dec

    return ct_dict

#--------------------------------------------------------------------------
#-- dither_convertion: update data dict dither amp and freq in degree based on amp and freq in asec
#--------------------------------------------------------------------------

def dither_convertion(ct_dict):
    """
    update data dict dither amp and freq in degree based on amp and freq in asec
    input:  ct_dict --- a dict of <param> <---> <information>
    output: ct_dict --- a dict with dither amp/freq in degreee updated
    """
    y_amp  = csd.convert_from_arcsec(ct_dict['y_amp_asec'][-1])
    y_freq = csd.convert_from_arcsec(ct_dict['y_freq_asec'][-1])
    z_amp  = csd.convert_from_arcsec(ct_dict['z_amp_asec'][-1])
    z_freq = csd.convert_from_arcsec(ct_dict['z_freq_asec'][-1])

    ct_dict['y_amp'][-1]  = y_amp
    ct_dict['y_freq'][-1] = y_freq
    ct_dict['z_amp'][-1]  = z_amp
    ct_dict['z_freq'][-1] = z_freq

    return ct_dict

#--------------------------------------------------------------------------
#-- create_display_obsid_list: create a list of obsids from form input   --
#--------------------------------------------------------------------------

def create_display_obsid_list(form, obsid):
    """
    create a list of obsids from form input for a parameter display page
    input:  form    --- data form
            obsid   --- the main obsid
    output: obsid_list  --- a list of obsids excluding the main obsid
    """
    obsids_list = []
    out         = form['obsids_list']

    if out != '':
#
#--- split the line into elements
#
        olist = re.split('\s+|,|:|;', out)
        tlist = []
        olen  = len(olist)
        for k in range(0, olen):
#
#--- if it is an empty element, skip
#
            ent = olist[k]
            if ent == '':
                continue
            else:
#
#--- if it is a positive integer, add to the list
#
                if ocf.is_neumeric(ent):
                    if int(ent) > 0: 
                        tlist.append(ent)
#
#--- if it is a negative interger, make a list between one before to this value
#--- example: (2222 -2224) will be [2222, 2223, 2224]
#
                    else:
                        slist = []
                        if k > 0:
                            for m in range(int(tlist[-1])+1, abs(int(ent)) +1):
                                slist.append(str(m))
                            tlist = tlist + slist
                        else:
                                slist.append(str(abs(int(ent))))
#
#--- if it is a '-', fill the list with value between one before and one after
#--- example: (2222 - 2224) will be [2222,2223, 2224]
#
                elif ent == '-':
                    for m in range(int(olist[k-1])+1, int(olist[k+1])):
                        tlist.append(str(m))

                else:
                    slist = []
                    mc = re.search('-', ent)
                    if mc is not None:
                        btemp = re.split('-', ent)
                        start = int(btemp[0])
#
#--- if a value is appended by '-', make a list between this one and one after
#--- example (2222- 2224) will be [2222, 2223, 2224]
#
                        if btemp[1] == '':
                            if  (k + 1) < olen:
                                for m in range(start, int(olist[k+1])):
                                    slist.append(str(m))
                            else:
                                slist.append(int(start))
#
#--- if it is a range, make a list between them
#--- example (2222-2224) will be [2222, 2223, 2224]
#
                        else:
                            stop  = int(btemp[1])
                            for m in range(start, stop+1):
                                slist.append(str(m))

                    tlist = tlist + slist

        tlist  = sorted(tlist)
        for ent in tlist:
            if ent == obsid:
                continue
            else:
                obsids_list.append(ent)

    return obsids_list

#--------------------------------------------------------------------------
#-- check_obsid_in_or_list: check whether obsids in obsids_ist are in active OR list
#--------------------------------------------------------------------------

def check_obsid_in_or_list(obsids_list):
    """
    check whether obsids in obsids_ist are in active OR list
    input:  obsids_list --- a list of obsids
    output: or_dict     --- a dict of <obsid> <--> 1/0, 1 for yes 0 for no
    """
    i_file  = obs_ss + 'scheduled_obs_list'
    data    = ocf.read_data_file(i_file)

    or_list = []
    for ent in data:
        atemp = re.split('\s+', ent)
        or_list.append(atemp[0])
    
    or_dict = {}
    for obsid in obsids_list:
        chk = 0
        if obsid in or_list:
            chk = 1
        or_dict[obsid]  = chk

    return or_dict

