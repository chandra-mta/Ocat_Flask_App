#################################################################################
#                                                                               #
#       express approval page                                                   #
#                                                                               #
#       author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                               #
#       last update: Aug 26, 2021                                               #
#                                                                               #
#################################################################################
import os
import sys
import re
import string
import Chandra.Time
import time
import numpy
from datetime       import datetime
import sqlite3 as sq
from contextlib import closing

from flask          import render_template, flash, redirect, url_for, session
from flask          import request, g, jsonify, current_app
from flask_login    import current_user

from cus_app            import db
from cus_app.models     import User, register_user 
from cus_app.express    import bp

import cus_app.supple.ocat_common_functions         as ocf
import cus_app.supple.read_ocat_data                as rod
import cus_app.ocatdatapage.create_selection_dict   as csd
import cus_app.ocatdatapage.update_data_record_file as udrf
#
#--- directory
#
basedir = os.path.abspath(os.path.dirname(__file__))
#
#--- current chandra time
#
now    = int(Chandra.Time.DateTime().secs)
today  = ocf.convert_chandra_time_to_display2(now, tformat='%m/%d/%y')

null_list  = [None, 'NA', 'NULL', 'None', 'null', 'none', '', '<Blank>']

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
#-- index: this is the main function to dispaly express submission page          --
#----------------------------------------------------------------------------------

@bp.route('/',      methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    current_app.logger.info(f"Opening Express")
#
#--- showing the status of input obsids (page 2)
#
    if 'submit_test' in request.form.keys():
        obsids_input         = request.form['obsid_list']
#
#--- obsid_list: a list of valid obsids 
#--- warning:    a list of obsids which are not formatted correctly
#
        obsid_list, warning  = separate_obsids(obsids_input)
#
#-- add the status of obsids such as whether already in approved list
#-- o_list: a  list of obsids which can be approved
#
        obsids_info, o_list  = check_obsid_status(obsid_list)

        return render_template('express/index.html',
                                stage = 1,
                                obsids_input = obsids_input,
                                obsids_info  = obsids_info,
                                warning      = warning
                              )
#
#--- open finalized page after updating approved data file etc (page 3)
#
    elif 'finalize' in request.form.keys():

        obsids_input         = request.form['obsids_input']
        obsid_list, warning  = separate_obsids(obsids_input)
        obsids_info, o_list  = check_obsid_status(obsid_list)
#
#--- missed: a list of obsids which do not meet the condition for approval
#
        missed = numpy.setdiff1d(obsid_list, o_list)
#
#--- approve obsids in the list
#
        if len(o_list) > 0:
            for obsid in o_list:
                approve_obsid(obsid)

        return render_template('express/index.html',
                                stage  = 2,
                                o_list = o_list,
                                m_list = missed
                              )
#
#--- opening starting obsid input page (page 1)
#
    else:
#
#--- if obsid list is remembered, pass it back to the input field
#
        if 'obsids_input' in request.form.keys():
            obsids_input = request.form['obsids_input']
        else:
            obsids_input = ''

        return render_template('express/index.html',
                                stage = 0,
                                obsids_input = obsids_input
                              )

#----------------------------------------------------------------------------------
#-- separate_obsids: convert a string of obsid sequences into a list             --
#----------------------------------------------------------------------------------

def separate_obsids(line):
    """
    convert a string of obsid sequences into a list
    input:  line        --- a string of the obsid sequences 
    output: obsid_list  --- a list of obsids
            warning     --- a list of entries which are not correctly formated
    """
#
#--- remove extra white space, and convert delimiters to a single space
#
    line  = re.sub('\s+-\s+', '-', line)
    line  = re.sub('-\s+',    '-', line)
    line  = re.sub('\s+-',    '-', line)
    line  = line.replace(':',   ' ')
    line  = line.replace(';',   ' ')
    line  = line.replace(',',   ' ')
    atemp = re.split('\s+', line)
#
#--- warning keeps irregular delimitting cases
#
    warning    = []
    obsid_list = []
    for ent in atemp:
#
#-- for the case that the entry is an sequence
#
        mc = re.search('-', ent)
        if mc is not None:
            btemp = re.split('-', ent)
            if ocf.is_neumeric(btemp[0]) and ocf.is_neumeric(btemp[1]):
                start = int(float(btemp[0]))
                stop  = int(float(btemp[1]))
                for k in range(start, stop+1):
                    obsid_list.append(str(k))
            else:
                warning.append(ent)
        else:
            if ocf.is_neumeric(ent):
                ent = str(int(float(ent)))
                obsid_list.append(ent)
            else:
                warning.append(ent)

    return obsid_list, warning

#----------------------------------------------------------------------------------
#-- check_obsid_status: create a list of lists of obsid status                   --
#----------------------------------------------------------------------------------

def check_obsid_status(obsid_list):
    """
    create a list of lists of obsid status
    input:  obsid_list      --- a list of obsids
    output: checked_list    --- a list of information about obsids:
                [<obsid>, <proposal ID>, <sequence #>, <title>, <target name>, <PI name>, <status>]
                status: 0       --- can be approved
                        1       --- already in approved list
                        <poc>   --- current user is not a POC initiated this sign-off process
                        2       --- obsid is not in the database
                        <status>--- status of the observation (e.g., observed, canceled, archived etc)
                        3       --- No assigned SI Mode so it cannot be approved
            o_list          --- a list of obsids which can be approved
    """
    user     = current_user.username
#
#--- read obsids in approved list
#
    ifile    = os.path.join(current_app.config['OCAT_DIR'], 'approved')
    out      = ocf.read_data_file(ifile)
    approved = []
    for ent in out:
        atemp = re.split('\s+', ent)
        approved.append(atemp[0])
    approved.reverse()
#
#--- read obsids in updates_table.db; create <obsid> <---> <poc> dict
#
    ufile    = os.path.join(current_app.config['OCAT_DIR'], 'updates_table.db')
#
#--- SQL query to database
#
    with closing(sq.connect(ufile)) as conn: # auto-closes
        with conn: # auto-commits
            with closing(conn.cursor()) as cur: # auto-closes
                fetch_result = cur.execute(f"SELECT obsidrev, submitter from revisions ORDER BY rev_time DESC").fetchall()
    updates  = {}
    for ent in fetch_result:
        obsid = str(ent[0]).split('.')[0]
        updates[obsid] = ent[1]

    checked_list = []
    o_list       = []
    for obsid in obsid_list:
#
#--- get information about the obsid
#
        info, status, si_mode = get_obsid_info(obsid)
#
#--- If the obsid does not have an assigned SI mode, then mark with 3, and it cannot be approved.
#
        if si_mode in null_list:
            info.append(3)
#
#--- if observation status is not unobserved or scheduled, mark it
#
        elif not (status in ['unobserved', 'scheduled', 'untriggered']):
            info.append(status)
#
#--- if the obsid is already in approved list, mark by 1
#
        elif obsid in approved:
            info.append(1)
#
#--- if poc who initiated the signoff is not the current user, mark by <poc>
#
        elif (obsid in updates.keys()) and (updates[obsid] != user):
            info.append(updates[obsid])
            o_list.append(obsid)
#
#--- otherwise marked by 0 
#
        else:
            if info[2] == '':
                info.append(2)          #--- obsid is not in the DB
            else:
                info.append(0)
                o_list.append(obsid)

        checked_list.append(info)

    return checked_list, o_list

#----------------------------------------------------------------------------------
#-- get_obsid_info: extract infornation about a given obsid                      --
#----------------------------------------------------------------------------------

def get_obsid_info(obsid):
    """
    extract infornation about a given obsid
    input:  obsid   --- obsid
    output: info_list   --- a list of:
            [<obsid>, <proposal ID>, <sequence #>, <title>, <target name>, <PI name>]
            status of the observation (e.g., unobserved, archived, canceled, etc)
    """
    try:
        p_dict = rod.read_ocat_data(obsid)
    except:
        return [obsid, '', '', '', '', ''], 'na'

    info_list   = []
    info_list.append(obsid)
    info_list.append(p_dict['proposal_number'])
    info_list.append(p_dict['seq_nbr'])
    info_list.append(p_dict['proposal_title'])
    info_list.append(p_dict['targname'])
    info_list.append(p_dict['pi_name'])

    return info_list, p_dict['status'], p_dict['si_mode']

#----------------------------------------------------------------------------------
#-- approve_obsid: approve the obsid                                             --
#----------------------------------------------------------------------------------

def approve_obsid(obsid):
    """
    approve the obsid 
    input:  obsid    --- obsid
    output: <ocat_dir>/approve
            <ocat_dir>/updates/<obsid>.<rev# + 1>
            various email send out 
    """
    asis  = 'asis'
    user  = current_user.username
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

    




























