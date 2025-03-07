#################################################################################################
#                                                                                               #
#           check_value_range.py: check whether the values are in the expected range            #
#                                                                                               #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                               #
#               last update Sep 13, 2021                                                        #
#                                                                                               #
#################################################################################################

import sys
import os
import re
import math
#
#--- read ocat parameter list
#
basedir = os.path.abspath(os.path.dirname(__file__))

import cus_app.supple.ocat_common_functions     as ocf

null_list = ['','N', 'NO', 'NULL', 'NA', 'NONE', 'n', 'No', 'Null', 'Na', 'None', None]

#-----------------------------------------------------------------------------------------------
#-- check_value_range: check whether the values are in the expected range                     --
#-----------------------------------------------------------------------------------------------

def check_value_range(ct_dict):
    """
    check parameter values are in the expected range, and if not, create warning texts.
    input:  ct_dict         --- a dict of <param> <---> <information>
    output: warning_list    --- a list of warning texts
    """
#
#---    read value checking conditions
#---    value_idct  --- a dict of parameter <--> [min, max]
#---    rank_dict   --- a dict of parameter <--> [min, max] but for rank entries
#---    group_list  --- a list of lists of grouped parameters
#---    rgroup_list --- a list of lists of grouped parameters for ranked entries
#---    exclude_list--- a list of two parameters which are exclusive
#
    value_dict, rank_dict, group_list, rgroup_list, exclude_list = read_condition_table()

    warning_list = []

    warning_list = instrument_check(ct_dict,   warning_list)
    warning_list = flag_change_check(ct_dict,  warning_list)
    warning_list = ra_dec_range_check(ct_dict, warning_list)
#
#--- neumeric value range check
#
    for param in value_dict.keys():
        if not param in ct_dict.keys():
            continue

        val = ct_dict[param][-1]
        if val in null_list:
            continue
        else:
            val = float(val)

        if val < value_dict[param][0] or val > value_dict[param][1]:
            name = ct_dict[param][0]
            note = param + ' (=' + str(val) + ') should be between '
            note = note  + str(value_dict[param][0]) + ' and ' + str(value_dict[param][1])  + '\n'
            warning_list.append(note)
#
#--- rank value check; mainly neumeric values
#
    for param in rank_dict.keys():
        for k in range(0, 10):
            name = ct_dict[param][0] + ' (rank: ' + str(k+1) + ')'
            val  = ct_dict[param][-1][k]
            if val in null_list:
                continue
            else:
                if ocf.is_neumeric(val):
                    val = float(val)
                else:
                    continue

            if val < rank_dict[param][0] or val > rank_dict[param][1]:
                note = name  + ' (=' + str(val) + ') should be between '
                note = note  + str(rank_dict[param][0]) + ' and ' 
                note = note  + str(rank_dict[param][1])  + '\n'
                warning_list.append(note)
#
#--- check all parameters in the group have values (or all na)
#
    for a_list in group_list:
        missing_list = check_param_value(a_list, ct_dict)
        mlen = len(missing_list)
        if mlen> 0:
            if mlen == 1:
                note = 'Please supply a value to: ' 
            else:
                note = 'Please supply values to: ' 
            for param in missing_list:
                note = note + '\n\t' + ct_dict[param][0]
            note = note + '\n'

            warning_list.append(note)
#
#--- ranked entry cases
#
    for a_list in rgroup_list:
        for k in range(0, 10):
            missing_list = check_param_value(a_list, ct_dict, k)
            if len(missing_list) > 0:
                for param in missing_list:
                    note = 'Please supply a value to: ' + ct_dict[param][0] 
                    note = note + ' (rank: ' + str(k+1) + ').\n';
                    warning_list.append(note)
#
#--- check mutually-exclusive parameters values
#
    for a_list in exclude_list:
        note = check_exclusitity(a_list, ct_dict)
        if note != '':
            warning_list.append(note)
     
    warning_list = frame_time_check(ct_dict,   warning_list)
    warning_list = targname_check(ct_dict,     warning_list)
    warning_list = grating_check(ct_dict,      warning_list)
    warning_list = hrc_si_check(ct_dict,       warning_list)
#
#--- time constraint tstart and tstop check
#
    note = compare_tstart_tstop(ct_dict)
    if not note == '':
        warning_list.append(note)
#
#--- remove empty lines
#
    cleaned = []
    for ent in warning_list:
        if ent.strip() == '':
            continue
        cleaned.append(ent)
        
    return cleaned

#-----------------------------------------------------------------------------------------------
#-- check_param_value: check if the first parameter has none-null value, whether 
#-- the rest have none-null data values
#-----------------------------------------------------------------------------------------------

def check_param_value(a_list, ct_dict, k=''):
    """
    check if the first parameter has none-null value, whether the rest have none-null data values
    we assume that the either all params has null data or non-null data.
    input:  ct_dict         --- a dict of <param> <---> <information>
            warning_list    --- a list of warning text
            k               --- rank. if '', no rank entry
    output: c_list          --- a list of parameters with null entries in the group
    """
    c_list = []
    if k == '':
        val = ct_dict[a_list[0]][-1]
    else:
        val = ct_dict[a_list[0]][-1][k]

    if not val in null_list:
        for param in a_list[1:]:
            if param in ct_dict.keys():
                if k == '':
                    val = ct_dict[param][-1]
                else:
                    val = ct_dict[param][-1][k]
                if val in ['', 'NA', None]:
                    c_list.append(param)

    return c_list

#-----------------------------------------------------------------------------------------------
#-- check_exclusitity: check two exclusive parameters have the values at the same time        --
#-----------------------------------------------------------------------------------------------

def check_exclusitity(a_list, ct_dict):
    """
    check two exclusive parameters have the values at the same time.
    input:  ct_dict         --- a dict of <param> <---> <information>
            warning_list    --- a list of warning text
    output: warning_list    --- an updated warning_list
    """
    note  = ''
    if len(a_list) > 1:
        val0  = ct_dict[a_list[0]][-1]
        val1  = ct_dict[a_list[1]][-1]
        name0 = ct_dict[a_list[0]][0]
        name1 = ct_dict[a_list[1]][0]
        if val0 in null_list:
            if val1 in null_list:
                note = name0 + ' or '  + name1 + ' should have a value (but not both).'
        else:
            if not val1 in null_list:
                note = name0 + ' and ' + name1 + ' cannot have values at the same time.'

    return note

#-----------------------------------------------------------------------------------------------
#-- ra_dec_range_check: check ra/dec parameter value ranges are in the expected range         --
#-----------------------------------------------------------------------------------------------

def ra_dec_range_check(ct_dict, warning_list):
    """
    check ra/dec parameter value ranges are in the expected range and also check 
    the large coordindate shift.
    input:  ct_dict         --- a dict of <param> <---> <information>
            warning_list    --- a list of warning text
    output: warning_list    --- an updated warning_list
    """
    ora       = ct_dict['dra'][-2]
    odec      = ct_dict['ddec'][-2]
    ora, odec = ocf.convert_ra_dec_format(ora, odec, oformat='dd')
    dra       = ct_dict['dra'][-1]
    ddec      = ct_dict['ddec'][-1]
    ra, dec   = ocf.convert_ra_dec_format(dra, ddec, oformat='dd')
    ora       = float(ora)
    odec      = float(odec)
    ra        = float(ra)
    dec       = float(dec)
#
#--- checking ra and dec values are in expected ranges
#
    note    = ''
    if ra < 0 or ra > 360:
        note = 'The value of RA is out of range. Please check the value.\n'

    if dec < -90 or dec > 90:
        note = 'The value of Dec is out of range. Please check the value.\n'
#
#--- check whether there is a large coordindate shift
#
    if note == '':
        diff      = math.sqrt((ora -ra)**2 + (odec - dec)**2)
        if diff > 0.1333:
            note = 'The coordinates were shifted by more than 8 arcmin.  You need CDO approval.\n'

    if note != '':
        warning_list.append(note)

    return warning_list

#-----------------------------------------------------------------------------------------------
#-- frame_time_check: check frame tie and most_efficientt parameter value codition            --
#-----------------------------------------------------------------------------------------------

def frame_time_check(ct_dict, warning_list):
    """
    check frame tie and most_efficientt parameter value codition.
    they are exclusive to each other and the both parameters cannot have values at the same time
    but one must have a value when the instrument is acis

    input:  ct_dict         --- a dict of <param> <---> <information>
            warning_list    --- a list of warning text
    output: warning_list    --- an updated warning_list
    """
    inst = ct_dict['instrument'][-1]
    if inst in ['ACIS-I', 'ACIS-S']: 
        note = check_exclusitity(['frame_time', 'most_efficient'], ct_dict)
        warning_list.append(note)

    return warning_list

#-----------------------------------------------------------------------------------------------
#-- targname_check: check whether the target name is modified and create a warning text       --
#-----------------------------------------------------------------------------------------------

def targname_check(ct_dict, warning_list):
    """
    check whether the target name is modified and create a warning text
    input:  ct_dict         --- a dict of <param> <---> <information>
            warning_list    --- a list of warning text
    output: warning_list    --- an updated warning_list
    """
    if ct_dict['targname'][-2]  != ct_dict['targname'][-1]:
        note = 'The target name was updated. MP will be notified this change.\n'
        warning_list.append(note)

    return warning_list

#-----------------------------------------------------------------------------------------------
#-- grating_check: check whether the grating is updated and create a warning text             --
#-----------------------------------------------------------------------------------------------

def grating_check(ct_dict, warning_list):
    """
    check whether the grating is updated and create a warning text
    input:  ct_dict         --- a dict of <param> <---> <information>
            warning_list    --- a list of warning text
    output: warning_list    --- an updated warning_list
    """
    if ct_dict['grating'][-2] != ct_dict['grating'][-1]:
        note = 'The grating was updated. This Change requires CDO approval.\n'
        warning_list.append(note)

    return warning_list

#-----------------------------------------------------------------------------------------------
#-- hrc_si_check: check whether hrc si mode is set if the inst is hrc                         --
#-----------------------------------------------------------------------------------------------

def hrc_si_check(ct_dict, warning_list):
    """
    check whether hrc si mode is set if the inst is hrc
    input:  ct_dict         --- a dict of <param> <---> <information>
            warning_list    --- a list of warning text
    output: warning_list    --- an updated warning_list
    """
    inst = ct_dict['instrument'][-1]
    if inst in ['HRC-I', 'HRC-S']:
        si_mode = ct_dict['hrc_si_mode'][-1]
        if si_mode in null_list:
            note = 'HRC SI Mode Is Not Provided.'
            warning_list.append(note)

    return warning_list

#-----------------------------------------------------------------------------------------------
#-- flag_change_check: check whether the section flags are changed, and create a warning text --
#-----------------------------------------------------------------------------------------------

def flag_change_check(ct_dict, warning_list):
    """
    check whether the section flags are changed, and create a warning text
    input:  ct_dict         --- a dict of <param> <---> <information>
            warning_list    --- a list of warning text
    output: warning_list    --- an updated warning_list
    """
    for flag in ['window_flag', 'roll_flag', 'dither_flag', 'spwindow_flag']:
        val0 =  ct_dict[flag][-2] 
        val1 =  ct_dict[flag][-1]

        if val0 in null_list and val1 in null_list:
            continue

        elif val0 != val1:
            note = ct_dict[flag][0] + ' was updated; this changes impacts constraints, and '
            note = note + 'you need a CDO approval for this change. If you already have '
            note = note + 'the permission, please indicate so in the comment section.\n'
            warning_list.append(note)

    return warning_list

#-----------------------------------------------------------------------------------------------
#-- instrument_check: check whether the instrument is changed and create a warning text       --
#-----------------------------------------------------------------------------------------------

def instrument_check(ct_dict, warning_list):
    """
    check whether the instrument is changed and create a warning text
    input:  ct_dict     --- a dict of <parameter> <---> <information>
            waring_list --- a list of warning text
    output: waring_list --- an updated warning_list
    """
    if ct_dict['instrument'][-2] != ct_dict['instrument'][-1]:
        note = 'The instrument was changed. '
        note = note + 'You need a CDO approval for this change. If you already have '
        note = note + 'the permission, please indicate so in the comment section.\n'
#
#--- if the instrument is change from acis to hrc or another way around, all parameter values
#--- of the original instrument are nullified; so notify that, too
#
        if ct_dict['instrument'][-2] in ['ACIS-I', 'ACIS-S']:
            if ct_dict['instrument'][-1] in ['HRC-I', 'HRC-S']:
                note = note + ' ALL ACIS PARAMETERS WERE NULLIFIED.'

        elif ct_dict['instrument'][-2] in ['HRC-I', 'HRC-S']:
            if ct_dict['instrument'][-1] in ['ACIS-I', 'ACIS-S']:
                note = note + ' ALL HRC PARAMETERS WERE NULLIFIED.'

        warning_list.append(note)

    return warning_list

#-----------------------------------------------------------------------------------------------
#-- read_condition_table: read value checking conditions                                      --
#-----------------------------------------------------------------------------------------------

def read_condition_table():
    """
    read value checking conditions
    input:  none but read from data files
    output: value_idct  --- a dict of parameter <--> [min, max]
            rank_dict   --- a dict of parameter <--> [min, max] but for rank entries
            group_list  --- a list of lists ofgrouped parameters
            rgroup_list --- a list of lists ofgrouped parameters for ranked entries
            exclude_list    --- a list of two parameters which are exclusive
                                (currently exclude_list is not used)
    """
#
#--- a range of a param with a neumeric values
#
    ifile  = os.path.join(basedir, '../static/ocatdatapage/value_ranges')
    data  = ocf.read_data_file(ifile)

    value_dict = {}
    rank_dict  = {}
    for ent in data:
        if ent[0] == '#':
            continue

        atemp = re.split(':', ent)
        param = atemp[0].strip()
        vmin  = float(atemp[1].strip()) 
        vmax  = float(atemp[2].strip()) 
        chk   = atemp[3].strip()
        if chk == 'v':
            value_dict[param] = [vmin, vmax]
        else:
            rank_dict[param]   = [vmin, vmax]
#
#--- a list of parameters that all must have values if at least one has a value
#
    ifile  = os.path.join(basedir, '../static/ocatdatapage/grouped_params')
    data  = ocf.read_data_file(ifile)

    group_list  = []
    rgroup_list = []
    for ent in data:
        atemp = re.split(':', ent)
        btemp = re.split('\s+', atemp[1])
        if atemp[0] == 's':
            group_list.append(btemp)
        else:   
            rgroup_list.append(btemp)
#
#--- a list of parameters if one has a value, other cannot has a value
#
    exclude_list = [[],]

    return value_dict, rank_dict, group_list, rgroup_list, exclude_list

#-----------------------------------------------------------------------------------------------
#-- compare_tstart_tstop: check whether tstart and tstop are properly set                     --
#-----------------------------------------------------------------------------------------------

def compare_tstart_tstop(ct_dict):
    """
    check whether tstart and tstop are properly set
    input:  ct_dict --- a dict of <param> <--> <information>
    output: note    --- a warning note
    """
    note = ''
    for k in range(0, 10):
        if ct_dict['tstart'][-1][k] in null_list:
            if ct_dict['tstop'][-1][k] in null_list:
                continue

            else:
                note = note + 'Tstart is not defined (rank=' + str(k+1) + ')\n'

        else:
            if ct_dict['tstop'][-1][k] in null_list:
                note = note + 'Tstop is not defined (rank=' + str(k+1) + ')\n'

            else:
                if ct_dict['tstart'][-1][k] > ct_dict['tstop'][-1][k]:
                    note = note + 'Tstart and Tstop on rank ' + str(k+1) 
                    note = note + ' are not properly set.\n'                

    return note

