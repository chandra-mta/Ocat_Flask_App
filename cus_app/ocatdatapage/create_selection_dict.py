#################################################################################################
#                                                                                               #
#   create_selection_dict.py: create a dict of p_id <--> [<p_id information>]                   #
#                                                                                               #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                               #
#               last update Sep 13, 2021                                                        #
#                                                                                               #
#################################################################################################

import sys
import os
import re
import time
import copy
import Chandra.Time
from flask import current_app

import cus_app.supple.ocat_common_functions     as ocf
import cus_app.supple.read_ocat_data            as rod
#
#--- reading directory list
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
#---- choices of pulldown fields. 
#
choice_npy  = (('NA', 'NA'), ('N', 'NO'), ('P','PREFERENCE'), ('Y','YES'),)
choice_ny   = (('N','NO'), ('Y','YES'),)
choice_nny  = (('NA', 'NA'), ('N', 'NO'), ('Y', 'YES'),)
choice_cp   = (('Y','CONSTRAINT'),('P','PREFERENCE'),)
choice_nncp = (('NA','NA'),('N','NO'), ('P','PREFERENCE'), ('Y', 'CONSTRAINT'),)

null_list   = ['','N', 'NO', 'NULL', 'NA', 'NONE', 'n', 'No', 'Null', 'Na', 'None', None]
#
#--- current chandra time
#
now    = Chandra.Time.DateTime().secs
#
#--- define several data lists
#
time_list = ['window_constraint', 'tstart', 'tstop', \
             'tstart_month', 'tstart_date', 'tstart_year', 'tstart_time',\
             'tstop_month',  'tstop_date',  'tstop_year',  'tstop_time',]

tsht_list = ['window_constraint', 'tstart', 'tstop']

roll_list = ['roll_constraint', 'roll_180', 'roll', 'roll_tolerance',]

awin_list = ['chip',  'start_row', 'start_column',\
              'height', 'width', 'lower_threshold', 'pha_range', 'sample',] 

rank_list = time_list + roll_list + awin_list

#-----------------------------------------------------------------------------------------------
#-- create_selection_dict: create a dict of p_id <--> [<label>, <selection>, <selectiontye>...]
#-----------------------------------------------------------------------------------------------

def create_selection_dict(obsid):
    """
    input:  obsid
    output: p_dict --- a dictioinary of <p_id> 
                            <--> [<label>, <selection>, <selection type>,<group>, <org value>, <value>]
                        label           a discriptive name of the parameter
                        selection:      blank space, or a list of [(param, display name),...]
                        selection type: n       --- non-editable/not to display
                                        v       --- open value 
                                        l       --- a list of choices
                        group:          gen     --- general
                                        dt      --- dither
                                        tc      --- time constraints
                                        rc      --- roll constraints
                                        oc      --- other constraints
                                        hrc     --- HRC
                                        acis    --- ACIS
                                        awin    --- ACIS Window
                                        too     --- TOO
                                        remarks --- Remarks and Comments
                                        rest    --- All others
                                        nu      --- Not Used
                        org value       the value of parameter extracted from the database
                        value           the updated value 
    """
#
#--- get the values from the database
#
    ct_dict = rod.read_ocat_data(obsid)
    p_dict  = {}
#
#---  general parameters; non editable entries
#
    p_id         = 'seq_nbr'
    label        = 'Sequence Number'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'targid' 
    label        = 'Target ID'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'status'
    label        = 'Status'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'obsid'
    label        = 'Obsid'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'proposal_number'
    label        = 'Proposal Number'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'proposal_title'
    label        = 'Proposal Title'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'obs_ao_str'
    label        = 'Obs AO Status' 
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'si_mode'
    label        = 'SI Mode'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'aca_mode'
    label        = 'ACA Mode'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'pi_name'
    label        = 'PI Name'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'observer'
    label        = 'Observer'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'approved_exposure_time'
    label        = 'Exposure Time'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    vals         = adjust_dicimal(vals, dic=1)
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'rem_exp_time'
    label        = 'Remaining Exposure Time'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = float(ct_dict[p_id])
    if vals < 0:
        vals     = '0.0'
    else:
        vals     = adjust_dicimal(vals, dic=1)
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'proposal_joint'
    label        = 'Joint Proposal'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'proposal_hst'
    label        = 'HST Approved Time'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'proposal_noao'
    label        = 'NOAO Approved Time'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'proposal_xmm'
    label        = 'XMM Approved Time'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'proposal_rxte'
    label        = 'RXTE Approved Time'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'proposal_vla'
    label        = 'VLA Approved Time'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'proposal_vlba'
    label        = 'VLBA Approved Time'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'soe_st_sched_date'
    label        = 'Scheduled Date'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    vals         = time_format_convert_lts(vals)
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'lts_lt_plan'
    label        = 'LTS Date'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    vals         = time_format_convert_lts(vals)
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'soe_roll'
    label        = 'Roll Observed'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    if ocf.is_neumeric(vals):
        vals         = '%3.2f' % float(ct_dict[p_id])
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'planned_roll'
    label        = 'Planned Roll'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = find_planned_roll(obsid)
    p_dict[p_id] = [label, choices, lind, group, vals, vals]
#
#--- general parameter; editable entries
#
    p_id         = 'instrument'
    label        = 'Instrument'
    choice       = ('ACIS-I', 'ACIS-S', 'HRC-I', 'HRC-S')
    choices      = [(x, x) for x in choice]
    lind         = 'l'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'grating'
    label        = 'Grating'
    choice       = ('NONE', 'LETG', 'HETG')
    choices      = [(x, x) for x in choice]
    lind         = 'l'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'type'
    label        = 'Type'
    choice       = ('GO', 'TOO', 'GTO', 'CAL', 'DDT', 'CAL_ER', 'ARCHIVE', 'CDFS')
    choices      = [(x, x) for x in choice]
    lind         = 'l'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'targname'
    label        = 'Target Name'
    choices      = ''
    lind         = 'v'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'ra'
    label        = 'RA'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    try:
        vals     = f"{round(float(ra),6):3.6f}"
    except:
        if vals not in null_list:
            #Invalid string
            raise Exception(f"Fetched RA value invalid: {vals}")

    ra           = vals
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'dec'
    label        = 'Dec'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    try:
        vals     = f"{round(float(ra),6):3.6f}"
    except:
        if vals not in null_list:
            #Invalid string
            raise Exception(f"Fetched DEC value invalid: {vals}")
    dec          = vals
    p_dict[p_id] = [label, choices, lind, group, vals, vals]
#
#--- converting ra/dec display format
#
    tra, tdec    = ocf.convert_ra_dec_format(ra, dec)

    p_id         = 'dra'
    label        = 'RA (HMS)'
    choices      = ''
    lind         = 'v'
    group        = 'gen'
    vals         = tra
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'ddec'
    label        = 'Dec (DMS)'
    choices      = ''
    lind         = 'v'
    group        = 'gen'
    vals         = tdec
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'y_det_offset'
    label        = 'Offset: Y'
    choices      = ''
    lind         = 'v'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'z_det_offset'
    label        = 'Offset: Z'
    choices      = ''
    lind         = 'v'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'trans_offset'
    label        = 'Z-Sim'
    choices      = ''
    lind         = 'v'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'focus_offset'
    label        = 'Sim-Focus'
    choices      = ''
    lind         = 'v'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'raster_scan'
    label        = 'Raster Scan'
    choices      = ''
    lind         = 'n'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'defocus'
    label        = 'Focus'
    choices      = ''
    lind         = 'v'
    group        = 'gen'
    vals         = ''
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'uninterrupt'
    label        = 'Uninterrupted Obs'
    choices      = choice_npy
    lind         = 'l'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'extended_src'
    label        = 'Extended SRC'
    choices      = choice_ny
    lind         = 'l'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'obj_flag'
    label        = 'Solar System Object'
    choice       = ('NO', 'MT', 'SS')
    choices      = [(x, x) for x in choice]
    lind         = 'l'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'object'
    label        = 'Object'
    group        = 'gen'
    choice       = ('NONE', 'NEW', 'COMET', 'EARTH', 'JUPITER', 'MARS',\
                    'MOON', 'NEPTUNE', 'PLUTO', 'SATURN', 'URANUS', 'VENUS')
    choices      = [(x, x) for x in choice]
    lind         = 'l'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'photometry_flag'
    label        = 'Photometry'
    choices      = choice_nny
    lind         = 'l'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'vmagnitude'
    label        = 'V Mag'
    choices      = ''
    lind         = 'v'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'est_cnt_rate'
    label        = 'Count Rate'
    choices      = ''
    lind         = 'v'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'forder_cnt_rate'
    label        = '1st Order Rate'
    choices      = ''
    lind         = 'v'
    group        = 'gen'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]
#
#---  Dither Parameters
#
    p_id         = 'dither_flag'
    label        = 'Dither'
    choices      = choice_nny
    lind         = 'l'
    group        = 'dt'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'y_amp'
    label        = 'Y_Amp (in degrees)'
    choices      = ''
    lind         = 'n'
    group        = 'dt'
    y_amp        = ct_dict[p_id]
    vals         = adjust_dicimal(y_amp)
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'y_amp_asec'
    label        = 'Y_Amp (in arcsec)'
    choices      = ''
    lind         = 'v'
    group        = 'dt'
    vals         = convert_to_arcsec(y_amp)
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'y_freq'
    label        = 'Y_Freq (in degrees/sec)'
    choices      = ''
    lind         = 'n'
    group        = 'dt'
    y_freq       = ct_dict[p_id]
    vals         = adjust_dicimal(y_freq)
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'y_freq_asec'
    label        = 'Y_Freq (in arcsec/sec)'
    choices      = ''
    lind         = 'v'
    group        = 'dt'
    vals         = convert_to_arcsec(y_freq)
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'y_phase'
    label        = 'Y_Phase'
    choices      = ''
    lind         = 'v'
    group        = 'dt'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'z_amp'
    label        = 'Z_Amp (in degrees)'
    choices      = ''
    lind         = 'n'
    group        = 'dt'
    z_amp        = ct_dict[p_id]
    vals         = adjust_dicimal(z_amp)
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'z_amp_asec'
    label        = 'Z_Amp (in arcsec)'
    choices      = ''
    lind         = 'v'
    group        = 'dt'
    vals         = convert_to_arcsec(z_amp)
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'z_freq'
    label        = 'Z_Freq (in degrees/sec)'
    choices      = ''
    lind         = 'n'
    group        = 'dt'
    z_freq       = ct_dict[p_id]
    vals         = adjust_dicimal(z_freq)
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'z_freq_asec'
    label        = 'Z_Freq (in arcsec/sec)'
    choices      = ''
    lind         = 'v'
    group        = 'dt'
    vals         = convert_to_arcsec(z_freq)
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'z_phase'
    label        = 'Z_Phase'
    choices      = ''
    lind         = 'v'
    group        = 'dt'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]
#
#--- Time Constraints

    p_id         = 'window_flag'
    label        = 'Window Flag'
    choices      = choice_ny
    lind         = 'l'
    group        = 'tc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'time_ordr'
    label        = 'Time Order' 
    choices      = ''
    lind         = 'v'
    group        = 'tc'
    vals         = ct_dict[p_id]
    time_ordr    = vals
    p_dict[p_id] = [label, choices, lind, group, vals, vals]
#
#--- set lists of yeas, month, and date for pulldown menus
#
    year         = ['NA'] + ocf.set_year_list(chk=1)
    month        = ('NA',  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',\
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
    date         = ['NA']
    for i in range(1, 32):
        date.append(ocf.add_leading_zero(i, 2))

    p_id         = 'window_constraint'
    label        = 'Window Constraint'
    choices      = choice_nncp
    lind         = 'l'
    group        = 'tc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'tstart'
    label        = 'Tstart'
    choices      = [(x, x) for x in month]
    lind         = 'l'
    group        = 'tc'
    vals         = ct_dict[p_id]
    tstart       = vals
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    start_list   = separate_time_to_rank(tstart)

    p_id         = 'tstop'
    label        = 'Tstop'
    choices      = [(x, x) for x in date]
    lind         = 'l'
    group        = 'tc'
    vals         = ct_dict[p_id]
    tstop        = vals
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    stop_list    = separate_time_to_rank(tstop)

    p_id         = 'tstart_month'
    label        = 'Start Month'
    choices      = [(x, x) for x in month]
    lind         = 'l'
    group        = 'tc'
    vals         = start_list[1]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'tstart_date'
    label        = 'Start Date'
    choices      = [(x, x) for x in date]
    lind         = 'l'
    group        = 'tc'
    vals         = start_list[2]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'tstart_year'
    label        = 'Start Year'
    choices      = [(x, x) for x in year]
    lind         = 'l'
    group        = 'tc'
    vals         = start_list[0]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'tstart_time'
    label        = 'Start Time'
    choices      = ''
    lind         = 'v'
    group        = 'tc'
    vals         = start_list[3]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'tstop_month'
    label        = 'Stop Month'
    choices      = [(x, x) for x in month]
    lind         = 'l'
    group        = 'tc'
    vals         = stop_list[1] 
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'tstop_date'
    label        = 'Stop Date'
    choices      = [(x, x) for x in date]
    lind         = 'l'
    group        = 'tc'
    vals         = stop_list[2] 
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'tstop_year'
    label        = 'Stop Year'
    choices      = [(x, x) for x in year]
    lind         = 'l'
    group        = 'tc'
    vals         = stop_list[0]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'tstop_time'
    label        = 'Stop Time'
    choices      = ''
    lind         = 'v'
    group        = 'tc'
    vals         = stop_list[3] 
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]
#
#--- Roll Constraints
#
    p_id         = 'roll_flag'
    label        = 'Roll Flag'
    choices      = choice_ny
    lind         = 'l'
    group        = 'rc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'roll_ordr'
    label        = 'Roll Order'
    choices      = ''
    lind         = 'v'
    group        = 'rc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'roll_constraint'
    label        = 'Roll Angle Constraints'
    choices      = choice_nncp
    lind         = 'l'
    group        = 'rc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]
    
    p_id         = 'roll_180'
    label        = 'Roll_180'
    choices      = choice_nny
    lind         = 'l'
    group        = 'rc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'roll'
    label        = 'Roll'
    choices      = ''
    lind         = 'v'
    group        = 'rc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'roll_tolerance'
    label        = 'Roll Tolerance'
    choices      = ''
    lind         = 'v'
    group        = 'rc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]
#
#--- Other Constraints
#
    p_id         = 'constr_in_remarks'
    label        = 'Constraints in Remarks?'
    choices      = choice_npy
    lind         = 'l'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'phase_constraint_flag'
    label        = 'Phase Constraint'
    choices      = choice_nncp
    lind         = 'n'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'phase_epoch'
    label        = 'Phase Epoch'
    choices      = ''
    lind         = 'v'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'phase_period'
    label        = 'Phase Period'
    choices      = ''
    lind         = 'v'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'phase_start'
    label        = 'Phase Min'
    choices      = ''
    lind         = 'v'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'phase_start_margin'
    label        = 'Phase Min Error'
    choices      = ''
    lind         = 'v'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'phase_end'
    label        = 'Phase Max'
    choices      = ''
    lind         = 'v'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'phase_end_margin'
    label        = 'Phase Max Error'
    choices      = ''
    lind         = 'v'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'monitor_flag'
    label        = 'Monitoring Observation'
    choices      = choice_ny
    lind         = 'l'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]


    p_id         = 'monitor_series'
    label        = 'Monitoring Series'
    choices      = ''
    lind         = 'v'
    group        = 'oc'
    try:
        vals     = ct_dict[p_id][0][0]
    except:
        vals     = []
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'pre_id'
    label        = 'Follows ObsID#'
    choices      = ''
    lind         = 'v'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'pre_min_lead'
    label        = 'Follows Obs Min Int'
    choices      = ''
    lind         = 'v'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'pre_max_lead'
    label        = 'Follows Obs Max Int'
    choices      = ''
    lind         = 'v'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'multitelescope'
    label        = 'Coordinated Observation'
    choices      = choice_npy
    lind         = 'l'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'observatories'
    label        = 'Observatories'
    choices      = ''
    lind         = 'v'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'multitelescope_interval'
    label        = 'Max Coordination Offset'
    choices      = ''
    lind         = 'v'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'pointing_constraint'
    label        = 'Pointing Update'
    choices      = choice_nny
    lind         = 'l'
    group        = 'oc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]
#
#--- HRC Parameters
#
    p_id         = 'hrc_timing_mode'
    label        = 'HRC Timing Mode'
    choices      = choice_ny
    lind         = 'l'
    group        = 'hrc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id            = 'hrc_zero_block'
    label        = 'Zero Block'
    choices      = choice_ny
    lind         = 'l'
    group        = 'hrc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'hrc_si_mode'
    label        = 'SI Mode'
    choices      = ''
    lind         = 'v'
    group        = 'hrc'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'hrc_si_select'
    label        = 'HRC SI SELECT'
    choices      = [('n', 'NO'), ('y', 'YES')]
    lind         = 'l'
    group        = 'hrc'
    vals         = ''
    p_dict[p_id] = [label, choices, lind, group, vals, vals]
#
#--- ACIS Parameters
#
    p_id         = 'exp_mode'
    label        = 'ACIS Exposure Mode'
    choice       =  ('NA', 'TE', 'CC')
    choices      = [(x, x) for x in choice]
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

#    p_id         = 'fep'
#    label        = 'Fep'
#    choice       =  ('NA', 'TE', 'CC')
#    choices      = ''
#    lind         = 'n'
#    group        = 'acis'
#    vals         = ct_dict[p_id]
#    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'dropped_chip_count'
    label        = 'Dropped Chip Count'
    choice       =  ('NA', 'TE', 'CC')
    choices      = ''
    lind         = 'n'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'bep_pack'
    label        = 'Event TM Format'
    choice       =  ('NA', 'F', 'VF', 'F+B', 'G')
    choices      = [(x, x) for x in choice]
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'frame_time'
    label        = 'Frame Time'
    choices      = ''
    lind         = 'v'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'most_efficient'
    label        = 'Most Efficient'
    choices      = choice_nny
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]
#
#--- set chip selection list
#
    c_choices    =  (('NA', 'NA'), ('N','NO'), ('Y','YES'), ('O1','OPT1'),\
                     ('O2','OPT2'), ('O3', 'OPT3'), ('O4','OPT4'), ('O5','OPT5'),)

    p_id         = 'ccdi0_on'
    label        = 'I0'
    choices      = c_choices
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'ccdi1_on'
    label        = 'I1'
    choices      = c_choices
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'ccdi2_on'
    label        = 'I2'
    choices      = c_choices
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'ccdi3_on'
    label        = 'I3'
    choices      = c_choices
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'ccds0_on'
    label        = 'S0'
    choices      = c_choices
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'ccds1_on'
    label        = 'S1'
    choices      = c_choices
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'ccds2_on'
    label        = 'S2'
    choices      = c_choices
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'ccds3_on'
    label        = 'S3'
    choices      = c_choices
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'ccds4_on'
    label        = 'S4'
    choices      = c_choices
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'ccds5_on'
    label        = 'S5'
    choices      = c_choices
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'subarray'
    label        = 'Use Subarray'
    choices      = (('NONE', 'NONE'), ('N', 'NO'), ('Y', 'YES'),)
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'subarray_start_row'
    label        = 'Start'
    choices      = ''
    lind         = 'v'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'subarray_row_count'
    label        = 'Rows'  
    choices      = ''
    lind         = 'v'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'duty_cycle'
    label        = 'Duty Cycle'
    choices      = choice_nny
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'secondary_exp_count'
    label        = 'Number'
    choices      = ''
    lind         = 'v'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'primary_exp_time'
    label        = 'Tprimary'
    choices      = ''
    lind         = 'v'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'onchip_sum'
    label        = 'Onchip Summing'
    choices      = choice_nny
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'onchip_row_count'
    label        = 'Onchip Rows'
    choices      = ''
    lind         = 'v'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'onchip_column_count'
    label        = 'Onchip Columns'
    choices      = ''
    lind         = 'v'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'eventfilter'
    label        = 'Energy Filter'
    choices      = choice_nny
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'eventfilter_lower'
    label        = 'Lowest Energy'
    choices      = ''
    lind         = 'v'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'eventfilter_higher'
    label        = 'Energy Range'
    choices      = ''
    lind         = 'v'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'multiple_spectral_lines'
    label        = 'Multi Spectral Lines'
    choices      = choice_nny
    lind         = 'l'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'spectra_max_count'
    label        = 'Spectra Max Count'  
    choices      = ''
    lind         = 'v'
    group        = 'acis'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]
#
#--- ACIS Window Constraints
#
    choice       =  ('NA','I0', 'I1',  'I2', 'I3', 'S0', 'S1', 'S2', 'S3', 'S4', 'S5')
    a_choices    = [(x, x) for x in choice]

    p_id         = 'aciswin_no'
    label        = 'ACIS Window #'
    choices      = ''
    lind         = 'v'
    group        = 'awin'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'ordr'
    label        = 'Ordr'
    choices      = ''
    lind         = 'v'
    group        = 'awin'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

#    p_id         = 'aciswin_id'
#    label        = 'ACIS Window ID'
#    choices      = ''
#    lind         = 'l'
#    group        = 'awin'
#    vals         = ct_dict[p_id]
#    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

#    p_id         = 'include_flag'
#    label        = 'ACIS Window Flag'
#    choices      = ''
#    lind         = 'n'
#    group        = 'awin'
#    vals         = ct_dict[p_id]
#    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'chip'
    label        = 'Chip'
    choices      = a_choices
    lind         = 'l'
    group        = 'awin'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'start_row'
    label        = 'Start Row'
    choices      = ''
    lind         = 'v'
    group        = 'awin'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'start_column'
    label        = 'Start Column'
    choices      = ''
    lind         = 'v'
    group        = 'awin'
    vals         = ct_dict[p_id]
    group        = 'awin'
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'height'
    label        = 'Height'
    choices      = ''
    lind         = 'v'
    group        = 'awin'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'width'
    label        = 'Width'
    choices      = ''
    lind         = 'v'
    group        = 'awin'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'lower_threshold'
    label        = 'Lower Energy'
    choices      = ''
    lind         = 'v'
    group        = 'awin'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]


    p_id         = 'pha_range'
    label        = 'Energy Range'
    choices      = ''
    lind         = 'v'
    group        = 'awin'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]

    p_id         = 'sample'
    label        = 'Sample Rate'
    choices      = ''
    lind         = 'v'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, copy.deepcopy(vals)]
#
#--- TOO
#
    p_id         = 'tooid'
    label        = 'TOO ID'
    choices      = ''
    lind         = 'n'
    group        = 'too'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'too_trig'
    label        = 'TOO Trigger'
    choices      = ''
    lind         = 'n'
    group        = 'too'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'too_type'
    label        = 'TOO Type'
    choices      = ''
    lind         = 'n'
    group        = 'too'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'too_start'
    label        = 'TOO Start'
    choices      = ''
    lind         = 'n'
    group        = 'too'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'too_stop'
    label        = 'TOO Stop'
    choices      = ''
    lind         = 'n'
    group        = 'too'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'too_followup'
    label        = '# of Follow-up Observations'
    choices      = ''
    lind         = 'n'
    group        = 'too'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'too_remarks'
    label        = 'Too Remarks'
    choices      = ''
    lind         = 'n'
    group        = 'too'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'spwindow_flag'
    label        = 'Window Filter'
    group        = 'too'
    choices      = choice_nny
    lind         = 'l'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]
#
#--- Others 
#
    p_id         = 'description'
    label        = 'Description'
    choices      = ''
    lind         = 'n'
    group        = 'rest'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'total_fld_cnt_rate'
    label        = 'Total Fld Cnt Rate'
    choices      = ''
    lind         = 'n'
    group        = 'rest'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'group_id'
    label        = 'Group ID'
    choices      = ''
    lind         = 'n'
    group        = 'rest'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'group_obsid'
    label        = 'Group Obsids'
    choices      = ''
    lind         = 'n'
    group        = 'rest'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'remarks' 
    label        = 'Remarks'
    choices      = ''
    lind         = 'v'
    group        = 'remarks'
    vals         = ct_dict[p_id].replace('\"', '\'')
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'comments'
    label        = 'Comments'
    choices      = ''
    lind         = 'v'
    group        = 'remarks'
    vals         = ct_dict[p_id].replace('\"', '\'')
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'monitor_series'
    label        = 'Monitor Series'
    choices      = ''
    lind         = 'n'
    group        = 'rest'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]
#
#-- Not Used in Ocat Data Page
#
    p_id         = 'seg_max_num'
    label        = 'Seg Max Number'
    choices      = ''
    lind         = 'n'
    group        = 'nu'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'ocat_propid'
    label        = 'Ocat Proposal ID'
    choices      = ''
    lind         = 'n'
    group        = 'nu'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'acisid'
    label        = 'ACIS ID'
    choices      = ''
    lind         = 'n'
    group        = 'nu'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'hrcid'
    label        = 'HRC ID'
    choices      = ''
    lind         = 'n'
    group        = 'nu'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'mpcat_star_fidlight_file'
    label        = 'Fid Light File'
    choices      = ''
    lind         = 'n'
    group        = 'nu'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]

    p_id         = 'data_rights'
    label        = 'Data Rights'
    choices      = ''
    lind         = 'n'
    group        = 'nu'
    vals         = ct_dict[p_id]
    p_dict[p_id] = [label, choices, lind, group, vals, vals]
#
#--- add obsids_list; keeps a list of obsids for the case of multi obsid submission
#
    p_id         = 'obsids_list'
    label        = 'ObsIDs List'
    choices      = ''
    lind         = 'n'
    vals         = ''
    p_dict[p_id] = [label, choices, lind, group, vals, vals]
#
#--- creating image link data
#
    part = 'https://cxc.harvard.edu/targets/'  + str(ct_dict['seq_nbr']) + '/'
    part = part + str(ct_dict['seq_nbr'])      + '.' + str(ct_dict['obsid'])   + '.'

    rass = "NoImage"
    rosat = "NoImage"
    dss = "NoImage"
    if os.path.isdir(f"/data/targets/{str(ct_dict['seq_nbr'])}"):
        test = ''.join([each for each in os.listdir(f"/data/targets/{str(ct_dict['seq_nbr'])}") if each.endswith('.gif')])
        
        if 'soe.rass.gif' in test:
            rass  = part + 'soe.rass.gif'
        elif 'rass.gif' in test:
            rass  = part + 'rass.gif'

        if 'soe.pspc.gif' in test:
            rosat  = part + 'soe.pspc.gif'
        elif 'pspc.gif' in test:
            rosat  = part + 'pspc.gif'

        if 'soe.dss.gif' in test:
            dss   = part + 'soe.dss.gif'
        elif 'dss.gif' in test:
            dss   = part + 'dss.gif'

    p_dict['rass']  = ['RASS',  '', 'n', rass,  rass]
    p_dict['rosat'] = ['ROSAT', '', 'n', rosat, rosat]
    p_dict['dss']   = ['DSS',   '', 'n', dss,   dss]
#
#--- creating acis/hrc section open indicators
#
    inst = ct_dict['instrument']
    if inst in ['HRC-I', 'HRC-S']:
        p_dict['hrc_open']  = ['HRC',  '', 'n', 'open',  'open']
        p_dict['acis_open'] = ['ACIS', '', 'n', 'close', 'close']
    else:
        p_dict['hrc_open']  = ['HRC',  '', 'n', 'close', 'close']
        p_dict['acis_open'] = ['ACIS', '', 'n', 'open',  'open']

#
#--- check whether obsid is in approved list
#
    obsid = int(p_dict['obsid'][-1])
    ifile = os.path.join(current_app.config['OCAT_DIR'], 'approved')
    data  = ocf.read_data_file(ifile)

    chk   = 0
    data.reverse()
    for ent in data:
        atemp = re.split('\s+', ent)
        cobsid = int(float(atemp[0]))
        if obsid == cobsid:
            chk = 1
            break

    p_dict['approved'] = ['Approved', '', 'n', chk, chk]


    return p_dict  

#-----------------------------------------------------------------------------------------------
#-- time_format_convert_lts: change time format                                               --
#-----------------------------------------------------------------------------------------------

def time_format_convert_lts(ltime):
    """
    change time format from <yyyy-<mm>-<dd>T<hh>:<mm>:<ss> to <Mmm> <dd> <yyyy> <hh>:<mm><AM/PM>
    input:  time in <yyyy-<mm>-<dd>T<hh>:<mm>:<ss>
    output: time in <Mmm> <dd> <yyyy> <hh>:<mm><AM/PM>
    """
    if ltime in ['', None, 'None', 'NA']:
        return ltime

    mc    = re.search('T', ltime)
    if mc is not None:
        atemp = re.split('T', ltime)
        btemp = re.split('-', atemp[0])
        ctemp = re.split(':', atemp[1])
    
        lmon  = ocf.change_month_format(btemp[1])
    
        ltime = lmon + ' ' + str(int(btemp[2])) + ' ' + btemp[0] 
        if float(ctemp[0]) < 12:
            ltime = ltime + ', ' + ctemp[0] + ':' + ctemp[1] +  'AM'
        else:
            hh    = float(ctemp[0]) - 12
            tpart = ocf.add_leading_zero(hh, 2) + ':' + ctemp[1] 
            ltime = ltime + ', ' + tpart + 'PM'

    return ltime

#-----------------------------------------------------------------------------------------------
#-- convert_to_arcsec: convert degree value into arcsec                                       --
#-----------------------------------------------------------------------------------------------

def convert_to_arcsec(val):
    """
    convert degree value into arcsec
    input:  val --- value in degree
    output: val --- value in arcsec
    """
    if ocf.is_neumeric(val):
        val =  val * 3600.0
        val = float('%3.3f' % round(val, 3))

    return  val

#-----------------------------------------------------------------------------------------------
#-- convert_to_arcsec: convert degree value into arcsec                                       --
#-----------------------------------------------------------------------------------------------

def convert_from_arcsec(val):
    """
    convert arcsec value to degree
    input:  val --- value in arcsec
    output: val --- value in degree
    """
    if ocf.is_neumeric(val):
        val =  val / 3600.0
        val = float('%3.6f' % round(val, 6))

    return  val

#-----------------------------------------------------------------------------------------------
#-- adjust_dicimal: adjust to dicial to 'dic'                                                 --
#-----------------------------------------------------------------------------------------------

def adjust_dicimal(val, dic=4):
    """
    adjust to dicial to 'dic'
    input:  val --- numeric value
            dic --- diciaml point; default: 4
    output: val --- adjusted val
    """
    if ocf.is_neumeric(val):
        ichk = 0
        try:
            chk = val/3.0           #--- testing the input value is in float/int
        except:
            val  = float(val)
            ichk = 1

        fmt = '%3.' + str(dic) + 'f'
        val = fmt % (round(val, dic))
        if ichk == 1:
            val = str(val)

    return val

#-----------------------------------------------------------------------------------------------
#-- separate_time_to_rank: separeate ranked time input into lists of year, month and date     --
#-----------------------------------------------------------------------------------------------

def separate_time_to_rank(time_list):
    """
    separeate ranked time input into lists of year, month and date
    input:  time_list   --- a list of time
    output: y_list      --- a list of year (with <rank> elements)
            m_list      --- a list of month 
            d_list      --- a list of day
            t_list      --- a list of time 
    """
    y_list = []
    m_list = []
    d_list = []
    t_list = []
    for k in range(0, 10):
        tout = time_list[k]
        if ocf.is_neumeric(tout):
            out = ocf.convert_chandra_time_to_display(stime)
            y_list.append(out[0])
            m_list.append(ocf.change_month_format(out[1]))
            d_list.append(out[2])
            t_list.append(out[3])

        elif not  tout in null_list:
            atemp = re.split('T', tout)
            btemp = re.split('-', atemp[0])
            y_list.append(btemp[0])
            m_list.append(ocf.change_month_format(btemp[1]))
            d_list.append(btemp[2])
            t_list.append(atemp[1])

        else:
            y_list.append('NA')
            m_list.append('NA')
            d_list.append('NA')
            t_list.append('00:00:00')

    return [y_list, m_list, d_list, t_list]

#-----------------------------------------------------------------------------------------------
#-- find_planned_roll: read planned roll for a given obsid                                    --
#-----------------------------------------------------------------------------------------------

def find_planned_roll(obsid):    
    """
    read planned roll for a given obsid
    input:  obsid   --- obsid
    output: line    --- <lower roll angle> - <upper roll angle>
    """

    obsid    = int(obsid)
    roll_m1 = 'na'
    roll_m2 = 'na'

    ifile = os.path.join(current_app.config['OBS_SS'], 'mp_long_term')
    out   = ocf.read_data_file(ifile)
    for ent in out:
        atemp = re.split(':', ent)
        try:
            test = int(atemp[0])
        except:
            continue
        if obsid == test:
            roll_m1 = atemp[1]
            roll_m2 = atemp[2]
            break
    
    if roll_m1 == 'na':
        line = ''
    else:
        if float(roll_m1) > float(roll_m2):
            line = roll_m2 + '  -  ' + roll_m1
        else:
            line = roll_m1 + '  -  ' + roll_m2
    return line

#-----------------------------------------------------------------------------------------------
#-- create_warning_line: check the observation status and create warning                     ---
#-----------------------------------------------------------------------------------------------

def create_warning_line(obsid):
    """
    check the observation status and create warning
    input:  obsid   --- obsid
    output: line    --- if there is a possible porlem, a warning text. oterwise <blank>
    """
    line    = ''
    ct_dict = rod.read_ocat_data(obsid)
#
#--- observation status; if not unobserved or schedule, a warning is flashed
#
    if ct_dict['status'] in ['unobserved', 'scheduled', 'untriggered']:
        pass
    elif ct_dict['status'] in ['observed', 'archived', 'triggered']:
        line = 'This observation was already '+ ct_dict['status'].upper() + '.'
    else:
        line = 'This observation was '+ ct_dict['status'].upper() + '.'

        return line
#
#--- check lts/scheduled obseration date
#
    time_diff = 1e8
    lts_chk   = 0
    obs_date = ct_dict['soe_st_sched_date']
    if obs_date in null_list:
        obs_date = ct_dict['lts_lt_plan']
        lts_chk = 1

    if not obs_date in null_list:
        ltime     = time.strftime('%Y:%j:%H:%M:%S', time.strptime(obs_date, '%Y-%m-%dT%H:%M:%S'))
        stime     = Chandra.Time.DateTime(ltime).secs
        time_diff = stime - now

    inday = int(time_diff / 86400)
#
#--- check whether this observation is on OR list
#
    ifile = os.path.join(current_app.config['OBS_SS'], 'scheduled_obs_list')
    mp_list = ocf.read_data_file(ifile)
    mp_chk  = 0
    for ent in mp_list:
        atemp = re.split('\s+', ent)
        if atemp[0] == obsid:
            mp_chk = 1
            break
#
#--- for the case that lts date is passed but not observed yet
#
    if lts_chk > 0 and time_diff < 0:
        line = 'The scheduled (LTS) date of this observation was already passed.'

    elif lts_chk  == 0 and  inday == 0:
        line = 'This observation is scheduled for today.'
#
#--- less than 10 days to scheduled date
#
    elif time_diff < 864000:
#
#--- if the observation is on OR list
#
        if mp_chk > 0:
            if inday < 0:
                inday = 0

            if ct_dict['status'][-1] == 'scheduled':
                line = str(inday) 
                line = line  + 'days left to the scheduled date. You must get a permission '
                line = line  + 'from MP to modify entries '
                line = line  + ' (Scheduled on: ' + time_format_convert_lts(obs_date) + '.)'
            else:
                line = 'This observation is currently under review in an active OR list. ' 
                line = line + 'You must get a permission from MP to modify entries.'
                line = line + ' (LTS Date: '     + time_format_convert_lts(obs_date) + '.)'
#
#--- if the observation is not on the OR list yet
#
        else:
            if inday < 0:
                inday = 0
            if lts_chk > 0 and ct_dict['status'][-1] == 'unobserved':
                line = str(inday) + ' (LTS) days left, '
                line = line  + ' but the observation is not scheduled yet. '
                line = line  + ' You may want to check whether this is '
                line = line  + 'still a possible observaiton date with MP.'
            else:
                if ct_dict['status'][-1] in ['unobserved', 'scheduled', 'untriggered']:
                    line = line  + 'This observation is scheduled on ' 
                    line = line  + time_format_convert_lts(obs_date) + '.'
#
#--- if the observation is on OR list, but more than 10 days away
#
    elif mp_chk > 0:
        line = 'This observation is currently under review in an active OR list. ' 
        line = line + 'You must get a permission from MP to modify entries'
        if lts_chk == 1:
            line = line + ' (LTS Date: '     + time_format_convert_lts(obs_date) + '.)'
        else:
            line = line + ' (Scheduled on: ' + time_format_convert_lts(obs_date) + '.)'

    return line

#-----------------------------------------------------------------------------------------------
#-- nullify_entries: if inst is changed, nullify the values of the related parameters         --
#-----------------------------------------------------------------------------------------------

def nullify_entries(ct_dict):
    """
    if the instrument is changed from hrc to acis or another way around, nullify the values
    of the related parameters
    input:  ct_dict --- a dict of <param> <---> <information>
    output: ct_dict --- an updated data dict
    """
    oinst = ct_dict['instrument'][-2]
    ninst = ct_dict['instrument'][-1]
#
#--- the instrument was changed from hrc to acis
#
    if oinst in ['HRC-I', 'HRC-S']:
        if ninst in ['ACIS-I', 'ACIS-S']:
            for param in ['hrc_timing_mode', 'hrc_zero_block', 'hrc_si_mode']:
                ct_dict[param][-1] = 'NA'
#
#--- the instrument was changed from acis to hrc
#
    elif oinst in  ['ACIS-I', 'ACIS-S']:
        if ninst in ['HRC-I', 'HRC-S']:
            for param in ['exp_mode', 'dropped_chip_count', 'bep_pack', 'frame_time', 'most_efficient',\
                      'ccdi0_on', 'ccdi1_on','ccdi2_on','ccdi3_on',\
                      'ccds0_on', 'ccds1_on','ccds2_on','ccds3_on','ccds4_on','ccds5_on',\
                      'subarray', 'subarray_start_row', 'subarray_row_count', 'duty_cycle',\
                      'secondary_exp_count', 'primary_exp_time', 'onchip_sum', 'onchip_row_count',\
                      'onchip_column_count', 'eventfilter', 'eventfilter_lower', \
                      'eventfilter_higher', 'multiple_spectral_lines', 'spectra_max_count']:
                ct_dict[param][-1] = 'NA'
#
#--- acis window parameters are ranked entries
#
            n_list = []
            for k in range(0, 10):
                n_list.append('NA')

            for param in ['chip', 'start_row',\
                      'start_column', 'height', 'width', 'lower_threshold', 'pha_range', 'sample']:

                ct_dict[param][-1] = n_list

    return ct_dict

#--------------------------------------------------------------------------
#-- create_match_dict: create a dictonary containing whether org and new values are same
#--------------------------------------------------------------------------

def create_match_dict(ct_dict):
    """
    create a dictonary containing whether org and new values are same
    input:  ct_dict     --- a dict of <param> <--> <information>
    output: ind_dict    --- a dictionary of <param> <---> <ind>
                            ind = 0 if org != new
                                = 1 if org == new
    """
    ind_dict = {}
    for param in ct_dict.keys():
        if param in ['monitor_series',]:
            continue
#
#---  handle rank cases separately
#
        if param in rank_list:
            continue 
#
#--- single entry cases
# 
        else:
            org = ct_dict[param][-2]
            new = ct_dict[param][-1]
            ind = compare_values(org, new)

            ind_dict[param] = ind
#
#--- time window case
#
    ind_dict = rank_match_dict(ct_dict, ind_dict, time_list, 'time_ordr')
#
#--- roll window case
#
    ind_dict = rank_match_dict(ct_dict, ind_dict, roll_list, 'roll_ordr')
#
#--- acis window case
#
    ind_dict = rank_match_dict(ct_dict, ind_dict, awin_list, 'aciswin_no')

    return ind_dict

#--------------------------------------------------------------------------
#-- rank_match_dict:  create a dictonary containing whether org and new values are same for rank cases
#--------------------------------------------------------------------------

def rank_match_dict(ct_dict, ind_dict, r_list, r_param):
    """
    create a dictonary containing whether org and new values are same for rank cases
    input:  ct_dict     --- a dict of <param> <--> <information>
    output: ind_dict    --- a dictionary of <param> <---> <ind>
                            ind = 0 if org != new
                                = 1 if org == new
    """
    rank  = ct_dict[r_param][-2]
    nrank = ct_dict[r_param][-1]
    if nrank > rank:
        rank = nrank

    for param in r_list:
        m_list = []
        for k in range(0, rank):
            org = ct_dict[param][-2][k]
            new = ct_dict[param][-1][k]
            ind = compare_values(org, new)
            m_list.append(ind)

        for k in range(rank, 10):
            m_list.append(1)

        ind_dict[param] = m_list

    return ind_dict

#--------------------------------------------------------------------------
#-- compare_values: compare two org and new values                       --
#--------------------------------------------------------------------------

def compare_values(org, new):
    """
    compare two org and new values
    input:  org --- original value
            new --- updated value
    output: ind --- 1, if the value is the same, else, 0
    """
    org = adjust_value_for_test(org)
    new = adjust_value_for_test(new)

    if org == new:
        ind = 1
    else:
        ind = 0

    return ind

#--------------------------------------------------------------------------
#-- adjust_value_for_test: modify the value format for comparing test    --
#--------------------------------------------------------------------------

def adjust_value_for_test(val):
    """
    modify the value format for comparing test
    input:  val --- an original value
    output  val --- an adjusted test value
    """
    try:
        val = float(val)
        val = float('%3.4f' % round(val,4))
    except:
        if val in null_list:
            val = 'None'
        elif isinstance(val, list):
            pass
        else:
            val = strip_spaces(val)
            if val in null_list:
                val = 'None'

    return val

#--------------------------------------------------------------------------
#-- strip_spaces: remove all spaces and lower the character for comparison 
#--------------------------------------------------------------------------

def strip_spaces(line):
    """
    remove all spaces and lower the character for comparison
    input:  line    --- an original text
    output: text    --- a space stripped text
    """
    text = ''
    for ent in line:
        if ent.isalpha() or ent.isnumeric()\
             or (ent in ['+', '-', '=', '@', '#', '$', '%', '&', '*','(', ')']):
            text = text + ent.lower()

    return text
