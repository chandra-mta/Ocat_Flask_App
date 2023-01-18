#################################################################################
#                                                                               #
#       read_ocat_data.py: extract parameter values for a given obsid           #
#                                                                               #
#               author: t. isobe (tisobe@cfa.harvard.edu)                       #
#                                                                               #
#               last update: Oct 19, 2021                                       #
#                                                                               #
#################################################################################

import os
import sys
import re
import string
import random
import time
import copy

from . import ocat_common_functions     as ocf
from . import get_value_from_sybase     as gvs
#
#--- non data value list
#
non_list = [None, 'N', 'NA','N/A', 'None', 'NONE', 'Null', 'null', 'none', '']
na_list = []
for k in range(0,10):
    na_list.append('NA')

#--------------------------------------------------------------------------
#-- read_ocat_data: extract parameter values for a given obsid          ---
#--------------------------------------------------------------------------

def read_ocat_data(obsid):
    """
    extract parameter values for a given obsid
    input:  obsid   --- obsid
    output: p_dict  --- a dictionary of <param name> <--> <param value>

    Note: there are severl parameter names  different from those in the database:
                TOO/DDT: 'type','trig','start','stop','followup','remarks']
                        will be with prefix 'too_'
                HRC SI Mode: si_mode will be hrc_si_mode to distingush from ACIS si_mode
                Joint Prop: 'prop_num', 'title', 'joint' will be:
                            'proposal_number', 'proposal_titile', 'proposal_joint'
                            see prop_params for others.
    """
#
#--- extract general parameter data
#
    p_dict = general_params(obsid)
#
#--- monitor flag related parameter data
#
    s_dict = monitor_params(obsid, p_dict['pre_id'], p_dict['group_id'])
    p_dict.update(s_dict)
#
#-- extract roll related parameter data
#
    s_dict = roll_params(obsid)
    p_dict.update(s_dict)
#
#-- extract time contstraint related parameter data
#
    s_dict = time_constraint_params(obsid)
    p_dict.update(s_dict)
#
#-- extract TOO/DDT related parameter data 
#
    s_dict = too_ddt_params(p_dict['tooid'])
    p_dict.update(s_dict)
#
#-- extract HRC related parameter data 
#
    s_dict = hrc_params(p_dict['hrcid'])
    p_dict.update(s_dict)
#
#-- extract ACIS related parameter data 
#
    s_dict = acis_params(p_dict['acisid'])
    p_dict.update(s_dict)
#
#-- extract ACIS window related parameter data 
#
    s_dict = aciswin_params(obsid)
    p_dict.update(s_dict)
#
#--- extract phase related parameter data
#
    s_dict = phase_params(obsid)
    p_dict.update(s_dict)
#
#--- extract dether related parameter data
#
    s_dict = dither_params(obsid)
    p_dict.update(s_dict)
#
#--- extract SIM related parameter data
#
    s_dict = sim_params(obsid)
    p_dict.update(s_dict)
#
#--- extract SOE data
#
    s_dict = soe_params(obsid)
    p_dict.update(s_dict)
#
#--- extract current AO  data --- it could be different from the origianl AO #
#
    val = ao_params(p_dict['ocat_propid'])
    if val != '':
        p_dict['obs_ao_str'] = val
#
#--- extract proposal related parameter data
#
    s_dict = prop_params(p_dict['ocat_propid'])
    p_dict.update(s_dict)

    return p_dict

#--------------------------------------------------------------------------
#-- general_params: extract general parameter data                       --
#--------------------------------------------------------------------------

def general_params(obsid):
    """
    extract general parameter data 
    input:  obsid   --- obsid
    output: p_dict  --- a dictionary of <param name> <--> <param value>
    """
    p_list = ['obsid', 'targid', 'seq_nbr', 'targname', 'obj_flag', 'object', 'si_mode', \
      'photometry_flag', 'vmagnitude', 'ra', 'dec', 'est_cnt_rate', 'forder_cnt_rate',\
      'y_det_offset', 'z_det_offset', 'raster_scan', 'dither_flag', 'approved_exposure_time', \
      'pre_min_lead', 'pre_max_lead', 'pre_id', 'seg_max_num', 'aca_mode', \
      'phase_constraint_flag', 'ocat_propid', 'acisid', 'hrcid', 'grating', 'instrument', \
      'rem_exp_time', 'soe_st_sched_date', 'type', 'lts_lt_plan', 'mpcat_star_fidlight_file',\
      'status', 'data_rights', 'tooid', 'description', 'total_fld_cnt_rate', 'extended_src',\
      'uninterrupt', 'multitelescope', 'observatories', 'tooid', 'constr_in_remarks', \
      'group_id', 'obs_ao_str', 'roll_flag', 'window_flag', 'spwindow_flag', \
      'multitelescope_interval', 'pointing_constraint']
    plen   = len(p_list)
    p_dict = {}

    cmd    = 'select ' + convert_list_to_line(p_list) +  ' from target where obsid=' + str(obsid)
    out    = gvs.get_value_from_sybase(cmd)

    for k in range(0, plen):
        p_dict[p_list[k]] = out[0][k]
#
#--- read reamarks
#
    cmd   = 'select remarks from target where obsid=' + str(obsid)
    out   = gvs.get_value_from_sybase(cmd)
    line  = cleanup_remarks(out)

    p_dict['remarks'] = line
#
#--- read comments
#
    cmd   = 'select mp_remarks  from target where obsid=' + str(obsid)
    out   = gvs.get_value_from_sybase(cmd)
    line  = cleanup_remarks(out)

    p_dict['comments'] = line

    return p_dict

#--------------------------------------------------------------------------
#-- monitor_params: extract monitor flag related parameter data         --
#--------------------------------------------------------------------------

def monitor_params(obsid, pre_id, group_id):
    """
    extract monitor flag related parameter data
    input:  obsid       --- obsid
            pre_id      --- pre id
            group_id    --- group id
    output: p_dict      --- a dictionary of <param name> <--> <param value>
    """
    p_dict = {}
#
#--- setting monitor_flag is tricky; keep the order of checking
#
    if pre_id in non_list:
        p_dict['monitor_flag'] = 'N'
    else:
        p_dict['monitor_flag'] = 'Y'

    cmd = 'select distinct pre_id from target where pre_id=' + str(obsid)
    out = gvs.get_value_from_sybase(cmd)

    if len(out) != 0 and  len(out[0]) > 0:
        p_dict['monitor_flag'] = 'Y'
#
#--- if group_id is not NULL, monitor_flag is N
#
    if not group_id in non_list:
        p_dict['monitor_flag'] = 'N'
#
#--- group_id needs extra "" around it to work with the sybase extraction
# 
        cmd = 'select obsid from target where group_id ="' + str(group_id) + '"'
        out = gvs.get_value_from_sybase(cmd)
        o_list = []
        try:
            for ent in out:
                o_list.append(ent[0])
        except:
            pass
        p_dict['group_obsid'] = select_unobserved(o_list)

    else:
        p_dict['group_obsid'] = []
#
#--- if monitoring flag is Y, find which obsids are in the monitoring list
#
    if p_dict['monitor_flag'] == 'Y':
        r_list = series_rev(obsid)
        f_list = series_fwd(obsid)
        c_list = r_list + f_list
        c_list = sorted(list(set(c_list)))
#
#--- separate observed and unobserved monitor series obsids
#
        n_list = select_unobserved(c_list)
        p_dict['monitor_series'] = n_list
    else:
        p_dict['monitor_series'] = []

    return p_dict

#--------------------------------------------------------------------------
#-- select_unobserved: check status of obsids in the list and select only scheduled and unobserved
#--------------------------------------------------------------------------

def select_unobserved(o_list):
    """
    check status of obsids in the list and select only scheduled and unobserved
    input:  o_list  --- a list of obsids
    output: u_list  --- a list of obsids which are not obvered yet
    """
    u_list = []
    for obsid in o_list:
        cmd    = 'select status from target where obsid=' + str(obsid)
        out    = gvs.get_value_from_sybase(cmd)
        status = out[0][0]
        if status in ['unobserved', 'scheduled']:
            u_list.append(obsid)

    return u_list

#--------------------------------------------------------------------------
#-- roll_params: extract roll related parameter data                    --
#--------------------------------------------------------------------------

def roll_params(obsid):
    """
    extract roll related parameter data
    input:  obsid       --- obsid
    output: p_dict      --- a dictionary of <param name> <--> <param value>
    """
    p_list = ['roll_constraint', 'roll_180', 'roll', 'roll_tolerance']
    plen   = len(p_list)

    p_dict = {}
#
#--- we don't know how many orders of data will be there but it should not 
#--- be larger than 10 ranks; so create NULL dataset up to 10 ranks
#
    roll_ordr = 0
    r_list    = []
    for k in range(0, plen):
        r_list.append(copy.deepcopy(na_list))
#
#--- check order 1 to 10 in order
#
    for k in range(1, 10):
        cmd = 'select ' + convert_list_to_line(p_list) 
        cmd = cmd + ' from rollreq where ordr = ' + str(k) + ' and obsid=' + str(obsid)
        out = gvs.get_value_from_sybase(cmd)
   
        if len(out) > 0 and len(out[0]) > 0:
            roll_ordr = k
            for j in range(0, plen):
                r_list[j][k-1] = out[0][j]

    p_dict['roll_ordr'] = roll_ordr

    for k in range(0, plen):
        p_dict[p_list[k]] = r_list[k]

    return p_dict

#--------------------------------------------------------------------------
#-- time_constraint_params: extract time contstraint related parameter data
#--------------------------------------------------------------------------

def time_constraint_params(obsid):
    """
    extract time contstraint related parameter data
    input:  obsid       --- obsid
    output: p_dict      --- a dictionary of <param name> <--> <param value>
    """
# 
#--- handling of the time condstraint data are similar to those of roll order case
#
    p_list = ['window_constraint', 'tstart', 'tstop']
    plen   = len(p_list)
    p_dict = {}

    time_ordr = 0
    r_list    = []
    for k in range(0, plen):
        r_list.append(copy.deepcopy(na_list))
    
    for k in range(1, 10):
        cmd = 'select ' + convert_list_to_line(p_list) + ' from timereq where ordr =' + str(k)
        cmd = cmd + ' and obsid=' + str(obsid)    
        out = gvs.get_value_from_sybase(cmd)
     
        if len(out) > 0  and len(out[0]) > 0:
            time_ordr = k
            for j in range(0, plen):
                r_list[j][k-1] = out[0][j]

    p_dict['time_ordr'] = time_ordr

    for k in range(0, plen):
        p_dict[p_list[k]] = r_list[k]

    return p_dict

#--------------------------------------------------------------------------
#-- too_ddt_params: extract TOO/DDT related parameter data              --
#--------------------------------------------------------------------------

def too_ddt_params(tooid):
    """
    extract TOO/DDT related parameter data
    input:  tooid       --- too id
    output: p_dict      --- a dictionary of <param name> <--> <param value>
    """
    p_list = ['type','start','stop','followup']
    plen   = len(p_list)
    p_dict = {}
#
#--- too/ddt data have different paramter names in the dictionary from those of
#--- in the database to avoid mix-up of the parameter names
#
    if tooid in non_list:
        for k in range(0, plen):
            name = 'too_' + p_list[k]
            p_dict[name]  = 'NA'
            if name == 'too_followup':
                p_dict[name]  = ''

    else:
        cmd = 'select '+  convert_list_to_line(p_list) + ' from too where tooid=' + str(tooid)
        out = gvs.get_value_from_sybase(cmd)

        if len(out) > 0  and len(out[0]) > 0:
            for k in range(0, plen):
                name = 'too_' + p_list[k]
                p_dict[name]  = out[0][k]
#
#--- read trig (trigger condition) 
#
    cmd   = 'select trig from too where tooid=' + str(tooid)
    out   = gvs.get_value_from_sybase(cmd)
    line  = cleanup_remarks(out)

    p_dict['too_trig'] = line
#
#--- read reamarks
#
    cmd   = 'select remarks from too where tooid=' + str(tooid)
    out   = gvs.get_value_from_sybase(cmd)
    line  = cleanup_remarks(out)

    p_dict['too_remarks'] = line

    return p_dict

#--------------------------------------------------------------------------
#-- hrc_params: extract hrc related parameter data                      --
#--------------------------------------------------------------------------

def hrc_params(hrcid):
    """
    extract hrc related parameter data
    input:  hrcid       --- hrc id
    output: p_dict      --- a dictionary of <param name> <--> <param value>
    """
    p_list = ['hrc_zero_block','timing_mode','si_mode']
    plen   = len(p_list)
    p_dict = {}

    if hrcid in non_list:
        p_dict['hrc_zero_block']  = 'NA'
        p_dict['hrc_timing_mode'] = 'NA'
#
#--- use "hrc_si_mode" NOT "si_mode" to distingush from acis si_mode
#
        p_dict['hrc_si_mode']     = 'NA'
    else:
        cmd = 'select ' +  convert_list_to_line(p_list) + ' from hrcparam where hrcid=' + str(hrcid) 
        out = gvs.get_value_from_sybase(cmd)

        if len(out) > 0 and  len(out[0]) > 0:
            p_dict['hrc_zero_block']  = out[0][0]
            p_dict['hrc_timing_mode'] = out[0][1]
            p_dict['hrc_si_mode']     = out[0][2]

    return p_dict

#--------------------------------------------------------------------------
#-- acis_params: extract acis related parameter data                    --
#--------------------------------------------------------------------------

def acis_params(acisid):
    """
    extract acis related parameter data
    input:  acisid      --- acis id
    output: p_dict      --- a dictionary of <param name> <--> <param value>
    """
    p_list = ['exp_mode', 'ccdi0_on', 'ccdi1_on', 'ccdi2_on', 'ccdi3_on', 'ccds0_on', 'ccds1_on', \
        'ccds2_on', 'ccds3_on', 'ccds4_on', 'ccds5_on', 'bep_pack', 'onchip_sum', \
        'onchip_row_count', 'onchip_column_count', 'frame_time', 'subarray', 'subarray_start_row', \
        'subarray_row_count', 'duty_cycle', 'secondary_exp_count', 'primary_exp_time',\
        'eventfilter', 'eventfilter_lower', 'eventfilter_higher', 'most_efficient', \
        'dropped_chip_count', 'multiple_spectral_lines', 'spectra_max_count']
    plen   = len(p_list)
    p_dict = {}

    if acisid in non_list:
        for ent in p_list:
            p_dict[ent] = 'NA'
            if ent == 'primary_exp_time':
                p_dict[ent] = 'NA'
    else:
        cmd   = 'select ' + convert_list_to_line(p_list) 
        cmd   = cmd  +  ' from acisparam where acisid=' + str(acisid)
        out   = gvs.get_value_from_sybase(cmd)

        for k in range(0, plen):
            p_dict[p_list[k]] = out[0][k]

    return p_dict

#--------------------------------------------------------------------------
#-- aciswin_params: extract acis window related parameter data          --
#--------------------------------------------------------------------------

def aciswin_params(obsid):
    """
    extract acis window related parameter data
    input:  obsid       --- obsid
    output: p_dict      --- a dictionary of <param name> <--> <param value>
    """
    p_list = ['ordr', 'aciswin_id', 'start_row', 'start_column', 'width', 'height',\
              'lower_threshold', 'pha_range', 'sample', 'chip', 'include_flag']
    plen   = len(p_list)
    p_dict = {}
#
#--- initialize temp list of lists; aciswn related parameter have up to 10 ranks
#
    save   = []
    olen   = 0
    for k in range(0, plen):
        if p_list[k] == 'ordr':
            save.append(list(range(1, 11)))

        elif p_list[k] == 'start_row':
            save.append(set_default_list(1))

        elif p_list[k] == 'start_column':
            save.append(set_default_list(1))

        elif p_list[k] == 'width':
            save.append(set_default_list(1023))

        elif p_list[k] == 'height':
            save.append(set_default_list(1023))

        elif p_list[k] == 'lower_threshold':
            save.append(set_default_list(0.08))

        elif p_list[k] =='pha_range':
            save.append(set_default_list(13.0))

        elif p_list[k] == 'sample':
            save.append(set_default_list(0))

        else: 
            save.append(copy.deepcopy(na_list))
#
#--- check whether there is acis window data
#
    cmd = 'select ' +  convert_list_to_line(p_list) + ' from aciswin where obsid=' + str(obsid)
    out = gvs.get_value_from_sybase(cmd)
#
#--- extracted data are not ordered by rank; sorting data with rank 
#--- (the first entry of each data list)
#
    if len(out) > 0 and len(out[0]) > 0:
        olen   = len(out)
        t_dict = {}
        t_list = []
        for k in range(0, olen):
            var = out[k][0]
            t_dict[var] = out[k]
            t_list.append(var)
        t_list = sorted(t_list)
        out = []
        for var in t_list:
            out.append(t_dict[var])
#
#--- replace NULL data entries with valid data
#
        for j in range(0, olen):
            for k in range(0, plen):
                save[k][j] = out[j][k]
#
#--- save in dictionary
#
    p_dict['aciswin_no'] = olen

    for k in range(0, plen):
        p_dict[p_list[k]] = save[k]

    return p_dict

#--------------------------------------------------------------------------
#--------------------------------------------------------------------------
#--------------------------------------------------------------------------

def set_default_list(val):
    
    save = []
    for k in range(0, 10):
        save.append(val)

    return save
        
#--------------------------------------------------------------------------
#-- phase_params: extract phase related parameter data                  --
#--------------------------------------------------------------------------

def phase_params(obsid):
    """
    extract phase related parameter data
    input:  obsid       --- obsid
    output: p_dict      --- a dictionary of <param name> <--> <param value>
    """
    p_list = ['phase_period', 'phase_epoch', 'phase_start', 'phase_end',\
              'phase_start_margin', 'phase_end_margin']
    plen   = len(p_list)
    p_dict = {}

    cmd = 'select ' +  convert_list_to_line(p_list) + ' from phasereq where obsid=' + str(obsid)
    out = gvs.get_value_from_sybase(cmd)

    if len(out) > 0 and len(out[0]) > 0:
        for k in range(0, plen):
            p_dict[p_list[k]] = out[0][k]
    else:
        for k in range(0, plen):
            p_dict[p_list[k]] = 'NA'

    return p_dict

#--------------------------------------------------------------------------
#-- dither_params: extract dither related parameter data                --
#--------------------------------------------------------------------------

def dither_params(obsid):
    """
    extract dether related parameter data
    input:  obsid       --- obsid
    output: p_dict      --- a dictionary of <param name> <--> <param value>
    """
    p_list = ['y_amp','y_freq','y_phase','z_amp','z_freq', 'z_phase']
    plen   = len(p_list)
    p_dict = {}

    cmd    = 'select ' + convert_list_to_line(p_list) + ' from dither where obsid=' + str(obsid)
    out    = gvs.get_value_from_sybase(cmd)

    if len(out) > 0 and len(out[0]) > 0:
        for k in range(0, plen):
            p_dict[p_list[k]] = out[0][k]
    else:
        for k in range(0, plen):
            p_dict[p_list[k]] = 'NA'

    return p_dict

#--------------------------------------------------------------------------
#-- sim_params: extract sim related parameter data                     ---
#--------------------------------------------------------------------------

def sim_params(obsid):
    """
    extract sim related parameter data
    input:  obsid       --- obsid
    output: p_dict      --- a dictionary of <param name> <--> <param value>
    """
    p_list = ['trans_offset', 'focus_offset']
    plen   = len(p_list)
    p_dict = {}

    cmd = 'select trans_offset,focus_offset from sim where obsid=' + str(obsid)
    out = gvs.get_value_from_sybase(cmd)

    if len(out) > 0 and len(out[0]) > 0:
        for k in range(0, plen):
            p_dict[p_list[k]] = out[0][k]
    else:
        for k in range(0, plen):
            p_dict[p_list[k]] = 'NA'

    return p_dict

#--------------------------------------------------------------------------
#-- soe_params: extract soe data                                         --
#--------------------------------------------------------------------------

def soe_params(obsid):
    """
    extract soe data
    input:  obsid       --- obsid
    output: p_dict      --- a dictionary of <param name> <--> <param value>
    """
    cmd = 'select soe_roll from soe where obsid=' + str(obsid) 
    cmd = cmd + " and unscheduled='N'"
    out = gvs.get_value_from_sybase(cmd)

    p_dict = {}
    try:
        p_dict['soe_roll'] = out[0][0]
    except:
        p_dict['soe_roll'] =  'NA'

    return p_dict

#--------------------------------------------------------------------------
#-- ao_params: extract current ao  data                                  --
#--------------------------------------------------------------------------

def ao_params(ocat_prpid):
    """
    extract current ao  data
    it could be ''; so just return the value and if not '', replace the value
    in p_dict['obs_ao_str']
    input:  ocat_prpid  --- proposal id
    output: val         --- current ao status; could be ''
    """
    cmd = 'select ao_str from prop_info where ocat_propid=' + str(ocat_prpid)
    out = gvs.get_value_from_sybase(cmd)
    val = out[0][0]

    return val

#--------------------------------------------------------------------------
#-- prop_params: extract proposal related parameter data                 --
#--------------------------------------------------------------------------

def prop_params(ocat_prpid):
    """
    extract proposal related parameter data
    input:  ocat_prpid  --- proposal id
    output: p_dict      --- a dictionary of <param name> <--> <param value>
    """
    p_dict = {}
#
#--- Proposal Related Data
#
    cmd = 'select prop_num,title,joint  from prop_info where ocat_propid=' + str(ocat_prpid)
    out = gvs.get_value_from_sybase(cmd)

    p_dict['proposal_number'] = out[0][0]
    p_dict['proposal_title']  = out[0][1]
#
#--- output from 'joint' gives more than one info
#
    p_dict['proposal_joint']  = out[0][2]

    p_dict['proposal_hst']    =  'NA'
    p_dict['proposal_noao']   =  'NA'
    p_dict['proposal_xmm']    =  'NA'
    p_dict['proposal_rxte']   =  'NA'
    p_dict['proposal_vla']    =  'NA'
    p_dict['proposal_vlba']   =  'NA'
    if not p_dict['proposal_joint'] in non_list:
        try:
            p_dict['proposal_hst']    = out[0][3]
            p_dict['proposal_noao']   = out[0][4]
            p_dict['proposal_xmm']    = out[0][5]
            p_dict['proposal_rxte']   = out[0][6]
            p_dict['proposal_vla']    = out[0][7]
            p_dict['proposal_vlba']   = out[0][8]
        except:
            pass
#
#--- Proposer's Info
#
    cmd = 'select last  from view_pi where ocat_propid=' + str(ocat_prpid)
    out = gvs.get_value_from_sybase(cmd)
    p_dict['pi_name'] = out[0][0]

    cmd = 'select last from view_coi where ocat_propid=' + str(ocat_prpid)
    out = gvs.get_value_from_sybase(cmd)
    try:
        p_dict['observer'] = out[0][0]
#
#--- if no observer's name is given, use pi name
#
    except:
        p_dict['observer'] = p_dict['pi_name']

    return p_dict

#--------------------------------------------------------------------------
#-- convert_list_to_line: convert a list entries to a line separeted by ',' 
#--------------------------------------------------------------------------

def convert_list_to_line(d_list):
    """
    convert a list entries to a line separeted by ','
    input:  d_list  --- a list of parameter names
    output: line    --- a line of parameter names separated by ','
    """
    dlen  = len(d_list)
    dlen1 = dlen -1
    line  = ''
    for k in range(0, dlen):
        if k == dlen1:
            line = line + d_list[k] 
        else:
            line = line + d_list[k] + ',' 

    return line

#--------------------------------------------------------------------------
#-- series_rev: find obsids in the group backword                        --
#--------------------------------------------------------------------------

def series_rev(obsid):
    """
    find obsids in the group backword
    input:  obsid   --- main obsid
    output: a_list  --- a list of obsids
    """
    a_list = []

    cmd = 'select pre_id from target where obsid =' + str(obsid)
    out = gvs.get_value_from_sybase(cmd)
    try:
        val = out[0][0]
    except:
        val = ''

    while not val in non_list:
        a_list.append(str(val))
        cmd = 'select pre_id from target where obsid =' + str(val)
        out = gvs.get_value_from_sybase(cmd)
        try:
            val = out[0][0] 
        except:
            val = ''
        
    a_list = sorted(list(set(a_list)))

    return a_list

#--------------------------------------------------------------------------
#-- series_fwd: find obsids in the group forward                         --
#--------------------------------------------------------------------------

def series_fwd(obsid):
    """
    find obsids in the group forward
    input:  obsid   --- main obsid
    output: a_list  --- a list of obsids
    """
    a_list = []

    cmd = 'select obsid from target where pre_id =' + str(obsid)
    out = gvs.get_value_from_sybase(cmd)
    try:
        val = out[0][0]
    except:
        val = ''

    while not val in non_list:
        a_list.append(str(val))
        cmd = 'select obsid from target where pre_id =' + str(val)
        out = gvs.get_value_from_sybase(cmd)
        try:
            val = out[0][0]
        except:
            val = ''
        
    a_list = sorted(list(set(a_list)))

    return a_list

#--------------------------------------------------------------------------
#--------------------------------------------------------------------------
#--------------------------------------------------------------------------

def cleanup_remarks(out):

    try:
        line  = (out[0][0])
        if type(line) == 'bytes':
            line = line.decode('UTF-8')

        line  = line.replace("bytearray(b'", '')
        line  = line.replace('bytearray(b"', '')
        line  = line.replace("')", "")
        line  = line.replace('")', "")
        line  = line.replace('\\n', ' ' )
        line  = line.replace('\'', '\"')
        line  = line.replace('\\"', "'")
    except:
        line  = ''

    if line in non_list:
        line = ''

    return line

#--------------------------------------------------------------------------

#if __name__ == "__main__":
#
#    if len(sys.argv)  == 2:
#        obsid = sys.argv[1].strip()
#        p_dict = read_ocat_data(obsid)
#
#        k_list = p_dict.keys()
#
#        for name in k_list:
#            line = name + '<-->' + str(p_dict[name])
#            print(line)


