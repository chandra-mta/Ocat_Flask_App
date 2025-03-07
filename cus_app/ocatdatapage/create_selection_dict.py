"""
**create_selection_dict.py**: Create a dict of p_id <--> [<p_id information>]

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Mar 10, 2025

"""
import sys
import os
import re
import time
import copy
from cxotime import CxoTime
from datetime import datetime
import calendar
from flask import current_app

import cus_app.supple.ocat_common_functions     as ocf
import cus_app.supple.read_ocat_data            as rod
#
#--- reading directory list
#
basedir = os.path.abspath(os.path.dirname(__file__))
#
#---- choices of pulldown fields. 
#
_CHOICE_NNPY = (('NA', 'NA'), ('N', 'NO'), ('P','PREFERENCE'), ('Y','YES'),)
_CHOICE_NY   = (('N','NO'), ('Y','YES'),)
_CHOICE_NNY  = (('NA', 'NA'), ('N', 'NO'), ('Y', 'YES'),)
_CHOICE_CP   = (('Y','CONSTRAINT'),('P','PREFERENCE'),)
_CHOICE_NNPC = (('NA','NA'),('N','NO'), ('P','PREFERENCE'), ('Y', 'CONSTRAINT'),)

_YEAR_LIST = ['NA'] + [str(x + datetime.now().year) for x in range(-1,5)]
_YEAR_CHOICE = [(x,x) for x in _YEAR_LIST]
_MONTH_LIST = ['NA'] + calendar.month_abbr[1:]
_MONTH_CHOICE = [(x,x) for x in _MONTH_LIST]
_DAY_LIST = ['NA'] + [f"{x:02}" for x in range(1,32)]
_DAY_CHOICE = [(x,x) for x in _DAY_LIST]

#
#--- set chip selection list
#
_CHOICE_CHIP    =  (('NA', 'NA'), ('N','NO'), ('Y','YES'), ('O1','OPT1'),\
                    ('O2','OPT2'), ('O3', 'OPT3'), ('O4','OPT4'), ('O5','OPT5'),)
_CHOICE_WINDOW = [(x, x) for x in ('NA','I0', 'I1',  'I2', 'I3', 'S0', 'S1', 'S2', 'S3', 'S4', 'S5')]


null_list   = ['','N', 'NO', 'NULL', 'NA', 'NONE', 'n', 'No', 'Null', 'Na', 'None', None]
#
#--- current chandra time
#
now    = CxoTime().secs
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

_NON_EDIT_GEN_PARAM ={
    'seq_nbr':'Sequence Number',
    'targid':'Target ID',
    'status':'Status',
    'obsid':'Obsid',
    'proposal_number':'Proposal Number',
    'proposal_title':'Proposal Title',
    'obs_ao_str':'Obs AO Status',
    'si_mode':'SI Mode',
    'aca_mode':'ACA Mode',
    'pi_name':'PI Name',
    'observer':'Observer',
    'approved_exposure_time':'Exposure Time',
    'rem_exp_time':'Remaining Exposure Time',
    'proposal_joint':'Joint Proposal',
    'proposal_hst':'HST Approved Time',
    'proposal_noao':'NOAO Approved Time',
    'proposal_xmm':'XMM Approved Time',
    'proposal_rxte':'RXTE Approved Time',
    'proposal_vla':'VLA Approved Time',
    'proposal_vlba':'VLBA Approved Time',
    'soe_st_sched_date':'Scheduled Date',
    'lts_lt_plan':'LTS Date',
    'soe_roll':'Roll Observed',
}
_INPUT_EDIT_GEN_PARAM = {
    'targname':'Target Name',
    'y_det_offset':'Offset: Y',
    'z_det_offset':'Offset: Z',
    'trans_offset':'Z-Sim',
    'focus_offset':'Sim-Focus',
    'vmagnitude':'V Mag',
    'est_cnt_rate':'Count Rate',
    'forder_cnt_rate':'1st Order Rate',
}
# ruff: noqa
_CHOICE_EDIT_GEN_PARAM = {
    'instrument':{'label':'Instrument', 'select':[(x, x) for x in ('ACIS-I', 'ACIS-S', 'HRC-I', 'HRC-S')]},
    'grating':{'label':'Grating', 'select':[(x, x) for x in ('NONE', 'LETG', 'HETG')]},
    'type':{'label':'Type', 'select':[(x, x) for x in ('GO', 'TOO', 'GTO', 'CAL', 'DDT', 'CAL_ER', 'ARCHIVE', 'CDFS', 'CLP')]},
    'uninterrupt':{'label':'Uninterrupted Obs', 'select':_CHOICE_NNPY},
    'extended_src':{'label':'Extended SRC', 'select':_CHOICE_NY},
    'obj_flag':{'label':'Solar System Object', 'select':[(x, x) for x in ('NO', 'MT', 'SS')]},
    'object':{'label':'Object', 'select':[(x, x) for x in ('NONE', 'NEW','ASTEROID', 'COMET', 'EARTH', 'JUPITER', 'MARS','MOON', 'NEPTUNE', 'PLUTO', 'SATURN', 'URANUS', 'VENUS')]},
    'photometry_flag':{'label':'Photometry', 'select':_CHOICE_NNY},
}
# ruff: noqa
_INPUT_EDIT_OTHER_PARAM = {
    'phase_epoch':'Phase Epoch',
    'phase_period':'Phase Period',
    'phase_start':'Phase Min',
    'phase_start_margin':'Phase Min Error',
    'phase_end':'Phase Max',
    'phase_end_margin':'Phase Max Error',
    'pre_id':'Follows ObsID#',
    'pre_min_lead':'Follows Obs Min Int',
    'pre_max_lead':'Follows Obs Max Int',
    'observatories':'Observatories',
    'multitelescope_interval':'Max Coordination Offset',
}
# ruff: noqa
_CHOICE_EDIT_ACIS_PARAM = {
    'exp_mode':{'label':'ACIS Exposure Mode', 'select':[(x, x) for x in ('NA', 'TE', 'CC')]},
    'bep_pack':{'label':'Event TM Format', 'select':[(x, x) for x in ('NA', 'F', 'VF', 'F+B', 'G')]},
    'most_efficient':{'label':'Most Efficient', 'select':_CHOICE_NNY},
    'ccdi0_on':{'label':'I0', 'select':_CHOICE_CHIP},
    'ccdi1_on':{'label':'I1', 'select':_CHOICE_CHIP},
    'ccdi2_on':{'label':'I2', 'select':_CHOICE_CHIP},
    'ccdi3_on':{'label':'I3', 'select':_CHOICE_CHIP},
    'ccds0_on':{'label':'S0', 'select':_CHOICE_CHIP},
    'ccds1_on':{'label':'S1', 'select':_CHOICE_CHIP},
    'ccds2_on':{'label':'S2', 'select':_CHOICE_CHIP},
    'ccds3_on':{'label':'S3', 'select':_CHOICE_CHIP},
    'ccds4_on':{'label':'S4', 'select':_CHOICE_CHIP},
    'ccds5_on':{'label':'S5', 'select':_CHOICE_CHIP},
    'subarray':{'label':'Use Subaray', 'select':[('NONE', 'NONE'), ('N', 'NO'), ('CUSTOM', 'YES')]},
    'duty_cycle':{'label':'Duty Cycle', 'select':_CHOICE_NNY},
    'onchip_sum':{'label':'Onchip Summing', 'select':_CHOICE_NNY},
    'eventfilter':{'label':'Energy Filter', 'select':_CHOICE_NNY},
    'multiple_spectral_lines':{'label':'Multi Spectral Lines', 'select':_CHOICE_NNY},
}
# ruff: noqa
_INPUT_EDIT_ACIS_PARAM = {
    'frame_time':'Frame Time',
    'subarray_start_row':'Start',
    'subarray_row_count':'Rows',
    'secondary_exp_count':'Number',
    'primary_exp_time':'Tprimary',
    'onchip_row_count':'Onchip Rows',
    'onchip_column_count':'Onchip Columns',
    'eventfilter_lower':'Lowest Energy',
    'eventfilter_higher':'Energy Range',
    'spectra_max_count':'Spectra Max Count',
}
_INPUT_EDIT_ACISWIN_PARAM = {
    'aciswin_no':'ACIS Window #',
    'ordr':'Ordr',
    'start_row':'Start Row',
    'start_column':'Start Column',
    'height':'Height',
    'width':'Width',
    'lower_threshold':'Lower Energy',
    'pha_range':'Energy Range',
    'sample':'Sample Rate'
}
#-----------------------------------------------------------------------------------------------
#-- create_selection_dict: create a dict of p_id <--> [<label>, <selection>, <selectiontye>...]
#-----------------------------------------------------------------------------------------------

def create_selection_dict(obsid):
    """
    input:  obsid
    output: p_dict --- a dictionary of <p_id> 
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
    ct_dict = rod.read_ocat_data(obsid) #: Dictionary of current ocat values.
    p_dict  = {} #: Dictionary storing revision information.
#
#--- General Parameters; non editable entries
#
    for k,v in _NON_EDIT_GEN_PARAM.items():
        #: p_dict[p_id] = [label, selection, selection type, group, original value, update value (starts as original)]
        val = ct_dict.get(k)
        if isinstance(val, list):
            p_dict[k] = [v, None, 'n', 'gen', val, copy.deepcopy(val)]
        else:
            p_dict[k] = [v, None, 'n', 'gen', val, val]
#
#--- General Parameters; input text entries
#
    for k,v in _INPUT_EDIT_GEN_PARAM.items():
        #: p_dict[p_id] = [label, selection, selection type, group, original value, update value (starts as original)]
        val = ct_dict.get(k)
        if isinstance(val, list):
            p_dict[k] = [v, None, 'v', 'gen', val, copy.deepcopy(val)]
        else:
            p_dict[k] = [v, None, 'v', 'gen', val, val]
#
#--- General Parameter; choice editable entries
#
    for k,v in _CHOICE_EDIT_GEN_PARAM.items():
        #: p_dict[p_id] = [label, selection, selection type, group, original value, update value (starts as original)]
        val = ct_dict.get(k)
        if isinstance(val, list):
            p_dict[k] = [v.get('label'), v.get('select'), 'l', 'gen', val, copy.deepcopy(val)]
        else:
            p_dict[k] = [v.get('label'), v.get('select'), 'l', 'gen', val, val]
#
#--- General Parameters; special case
#
    val         = find_planned_roll(obsid)
    p_dict['planned_roll'] = ['Planned Roll', None, 'n', 'gen', val, val]

    tra, tdec    = ocf.convert_ra_dec_format(ct_dict.get('ra'), ct_dict.get('dec'), oformat="hmsdms")
    p_dict['dra'] = ['RA (HMS)', None, 'v', 'gen', tra, tra]
    p_dict['ddec'] = ['Dec (DMS)', None, 'v', 'gen', tdec, tdec]
#
#--- Dither Parameters; non editable entries
#
    p_id         = 'y_amp'
    val = ct_dict.get(p_id)
    p_dict[p_id] = ['Y_Amp (in degrees)', None, 'n', 'dt', val, val]

    p_id         = 'y_freq'
    val = ct_dict.get(p_id)
    p_dict[p_id] = ['Y_Freq (in degrees/sec)', None, 'n', 'dt', val, val]

    p_id         = 'z_amp'
    val = ct_dict.get(p_id)
    p_dict[p_id] = ['Z_Amp (in degrees)', None, 'n', 'dt', val, val]

    p_id         = 'z_freq'
    val = ct_dict.get(p_id)
    p_dict[p_id] = ['Z_Freq (in degrees/sec)', None, 'n', 'dt', val, val]
#
#--- Dither Parameters; input text entries
#
    p_id         = 'y_amp_asec'
    val         = convert_to_arcsec(ct_dict.get('y_amp'))
    p_dict[p_id] = ['Y_Amp (in arcsec)', None, 'v', 'dt', val, val]

    p_id         = 'y_freq_asec'
    val         = convert_to_arcsec(ct_dict.get('y_freq'))
    p_dict[p_id] = ['Y_Freq (in arcsec/sec)', None, 'v', 'dt', val, val]

    p_id         = 'y_phase'
    val = ct_dict.get(p_id)
    p_dict[p_id] = ['Y_Phase', None, 'v', 'dt', val, val]

    p_id         = 'z_amp_asec'
    val         = convert_to_arcsec(ct_dict.get('z_amp'))
    p_dict[p_id] = ['Z_Amp (in arcsec)', None, 'v', 'dt', val, val]

    p_id         = 'z_freq_asec'
    val         = convert_to_arcsec(ct_dict.get('z_freq'))
    p_dict[p_id] = ['Z_Freq (in arcsec/sec)', None, 'v', 'dt', val, val]

    p_id         = 'z_phase'
    val = ct_dict.get(p_id)
    p_dict[p_id] = ['Z_Phase', None, 'v', 'dt', val, val]
#
#--- Dither Parameters; choice editable entries
#
    p_id         = 'dither_flag'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Dither', _CHOICE_NY, 'l', 'dt', val, val]
#
#--- Time Constraints; choice editable entries
#
    p_id         = 'window_flag'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Window Flag', _CHOICE_NY, 't', 'tc', val, val]

    p_id         = 'window_constraint'
    val = ct_dict.get(p_id)
    p_dict[p_id] = ['Window Constraint', _CHOICE_NNPC, 'l', 'tc', val, val]

    p_id         = 'tstart'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Tstart', None, 'l', 'tc', val, copy.deepcopy(val)] #: None choices since this is not edited directly

    start_list   = separate_time_to_rank(ct_dict.get('tstart'))

    p_id         = 'tstop'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Tstop', None, 'l', 'tc', val, copy.deepcopy(val)] #: None choices since this is not edited directly

    stop_list    = separate_time_to_rank(ct_dict.get('tstop'))
#
#--- Time Constraints; Separate Date Selector
#
    p_id         = 'tstart_year'
    val         = start_list[0]
    p_dict[p_id] = ['Start Year', _YEAR_CHOICE, 'l', 'tc', val, copy.deepcopy(val)]

    p_id         = 'tstart_month'
    val         = start_list[1]
    p_dict[p_id] = ['Start Month', _MONTH_CHOICE, 'l', 'tc', val, copy.deepcopy(val)]

    p_id         = 'tstart_date'
    val         = start_list[2]
    p_dict[p_id] = ['Start Date', _DAY_CHOICE, 'l', 'tc', val, copy.deepcopy(val)]

    p_id         = 'tstop_year'
    val         = stop_list[0]
    p_dict[p_id] = ['Stop Year', _YEAR_CHOICE, 'l', 'tc', val, copy.deepcopy(val)]

    p_id         = 'tstop_month'
    val         = stop_list[1] 
    p_dict[p_id] = ['Stop Month', _MONTH_CHOICE, 'l', 'tc', val, copy.deepcopy(val)]

    p_id         = 'tstop_date'
    val         = stop_list[2] 
    p_dict[p_id] = ['Stop Date', _DAY_CHOICE, 'l', 'tc', val, copy.deepcopy(val)]

#
#--- Time Constraints; input text entries
#
    p_id         = 'time_ordr'
    val = ct_dict.get(p_id)
    p_dict[p_id] = ['Time Order', None, 'v', 'tc', val, val]

    p_id         = 'tstart_time'
    val         = start_list[3]
    p_dict[p_id] = ['Start Time', None, 'v', 'tc', val, copy.deepcopy(val)]

    p_id         = 'tstop_time'
    val         = stop_list[3] 
    p_dict[p_id] = ['Stop Time', None, 'v', 'tc', val, copy.deepcopy(val)]
#
#--- Roll Constraints; choice editable entries
#
    p_id         = 'roll_flag'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Roll Flag', _CHOICE_NNPY, 'l', 'rc', val, val]

    p_id         = 'roll_constraint'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Roll Angle Constraints', _CHOICE_NNPC, 'l', 'rc', val, copy.deepcopy(val)]

    p_id         = 'roll_180'
    vals         = ct_dict.get(p_id)
    p_dict[p_id] = ['Roll_180', _CHOICE_NNY, 'l', 'rc', val, copy.deepcopy(val)]
#
#--- Roll Constraints; input text entries
#
    p_id         = 'roll_ordr'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Roll Order', None, 'v', 'rc', val, copy.deepcopy(val)]

    p_id         = 'roll'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Roll', None, 'v', 'rc', val, copy.deepcopy(val)]

    p_id         = 'roll_tolerance'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Roll Tolerance', None, 'v', 'rc', val, copy.deepcopy(val)]
#
#--- Other Constraints; non editable entries
#
    p_id         = 'phase_constraint_flag'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Phase Constraint', None, 'n', 'oc', val, val]

    p_id         = 'monitor_series'
    vals     = ct_dict.get(p_id)
    p_dict[p_id] = ['Monitoring Series', None, 'n', 'oc', val, copy.deepcopy(val)]
#
#--- Other Constraints; choice editable entries
#
    p_id         = 'constr_in_remarks'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Constraints in Remarks?', _CHOICE_NNPY, 'l', 'oc', val, val]

    p_id         = 'monitor_flag'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Monitoring Observation', _CHOICE_NY, 'l', 'oc', val, val]

    p_id         = 'multitelescope'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Coordinated Observation', _CHOICE_NNPY, 'l', 'oc', val, val]

    p_id         = 'pointing_constraint'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Pointing Update', _CHOICE_NNY, 'l', 'oc', val, val]
#
#--- Other Constraints; input text entries
#
    for k,v in _INPUT_EDIT_OTHER_PARAM.items():
        val = ct_dict.get(k)
        if isinstance(val, list):
            p_dict[k] = [v, None, 'v', 'oc', val, copy.deepcopy(val)]
        else:
            p_dict[k] = [v, None, 'v', 'oc', val, val]
#
#--- HRC Parameters; choice editable entries
#
    p_id         = 'hrc_timing_mode'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['HRC Timing Mode', _CHOICE_NY, 'l', 'hrc', val, val]

    p_id         = 'hrc_zero_block'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Zero Block', _CHOICE_NY, 'l', 'hrc', val, val]
#
#--- HRC Parameters; input text entries
#
    p_id         = 'hrc_si_mode'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['SI Mode', None, 'l', 'hrc', val, val]
#
#--- ACIS Parameters; choice editable entries
#
    p_id         = 'dropped_chip_count'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Dropped Chip Count', None, 'n', 'acis', val, val]
#
#--- ACIS Parameters; choice editable entries
#
    for k,v in _CHOICE_EDIT_ACIS_PARAM.items():
        val = ct_dict.get(k)
        p_dict[k] = [v.get('label'), v.get('select'), 'l', 'acis', val, val]
#
#--- ACIS Parameters; input text entries
#
    for k, v in _INPUT_EDIT_ACIS_PARAM.items():
        val = ct_dict.get(k)
        p_dict[k] = [v, None, 'v', 'acis', val, val]
#
#--- ACIS Window Constraints; choice editable entries
#
    p_id         = 'chip'
    val         = ct_dict.get(p_id)
    p_dict[p_id] = ['Chip', _CHOICE_WINDOW, 'l', 'awin', val, copy.deepcopy(val)]
#
#--- ACIS Window Constraints; input text entries
#
    for k,v in _INPUT_EDIT_ACISWIN_PARAM.items():
        val = ct_dict.get(k)
        if isinstance(val, list):
            p_dict[k] = [v, None, 'v', 'awin', val, copy.deepcopy(val)]
        else:
            p_dict[k] = [v, None, 'v', 'awin', val, val]
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
    if time_list == None:
        real = 0
        placeholder = 10
    else:
        real = len(time_list)
        placeholder = 10 - real
    for k in range(real):
        atemp = time_list[k].split()
        m_list.append(atemp[0])
        d_list.append(f"{int(atemp[1]):02}")
        y_list.append(atemp[2])
        t_list.append(datetime.strptime(atemp[3], '%I:%M%p').strftime('%H:%M:%S'))

    for k in range(real,placeholder):
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
        stime     = CxoTime(ltime).secs
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
        if not ent.isspace():
            text = text + ent.lower()
    return text
