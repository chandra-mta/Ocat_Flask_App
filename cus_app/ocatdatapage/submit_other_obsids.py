#################################################################################################
#                                                                                               #
#       submit_other_obsids.py: update obsids on a list as the original obsid was updated       #
#                                                                                               #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                               #
#               last update Oct 22, 2021                                                        #
#                                                                                               #
#################################################################################################

import sys
import os
import re
import math
import time
import random
import Chandra.Time

import cus_app.supple.ocat_common_functions         as ocf
import cus_app.ocatdatapage.create_selection_dict   as csd
import cus_app.ocatdatapage.update_data_record_file as udrf
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

null_list = [None, 'NA', 'N', 'NULL', 'None', 'NONE',  'n', 'null', 'none', '', ' ']

time_list = ['window_constraint', 'tstart', 'tstop', \
              'tstart_month', 'tstart_date', 'tstart_year', 'tstart_time',\
              'tstop_month',  'tstop_date',  'tstop_year',  'tstop_time',]

roll_list = ['roll_constraint', 'roll_180', 'roll', 'roll_tolerance',]

awin_list = ['chip', 'start_row', 'start_column',\
              'height', 'width', 'lower_threshold', 'pha_range', 'sample',]

rank_list = time_list + roll_list + awin_list

skip_list = ['monitor_series', 'obsids_list', 'approved',\
             'group_obsid', 'dec', 'ra', 'acis_open', 'hrc_open'] + rank_list

now       = Chandra.Time.DateTime().secs

#-----------------------------------------------------------------------------------------------
#-- submit_other_obsids: update obsids on a list as the original obsid was updated            --
#-----------------------------------------------------------------------------------------------

def submit_other_obsids(obsids_list, oct_dict, oind_dict,  asis, user):
    """
    update obsids on a list as the original obsid was updated
    input:  obsids_list --- a list of obsids to be processed
            oct_dict    --- a dict of <param> <--> <information> of the original obsid
            oind_dict   --- a dict of <param> <--> 0 or 1 ; if 0, the vaule is updated
            asis        --- asis status
            user        --- poc user
    output: <data_dir>/updates/<obsid>.<rev#>
            <data_dir>/updates_table.list
            <data_dir>/approved (if asis == 'asis'/'remove')
            various eamil sent out
            note        --- a list of lists of notification
                        [[<coordindate shift>], [sch date <10days?>], [OR list?]]
            status      --- a list of statuses of the observations
            no_change   --- a list of obsids which parameter values were not updated
    """
#
#--- if it is a normal submission, find what were updated
#
    if asis == 'norm':
        diff_dict = {}
        for param in oind_dict.keys():
            if param in skip_list:
                continue
#
#--- 4th position of ct_dict is a group name such as gen, acis, hrc
#
            if oind_dict[param] == 0:
                diff_dict[param] = [oct_dict[param][-1], oct_dict[param][4]]

    note       = [[], [], []]
    no_change = []
    status     = []
    for obsid in obsids_list:
#
#--- create <param> <---> <information> dict for the new obsid
#
        ct_dict  = csd.create_selection_dict(obsid)
#
#--- process farther only if the status is 'unobserved' or 'scheduled'
#
        ostatus  = ct_dict['status'][-1]
        status.append(ostatus)
        if not (ostatus in ['unobserved', 'scheduled', 'untriggered']):
            continue
#
#--- if this is a normal update, update parameter values in the new obsid based on the original obsid
#
        if asis == 'norm':
#
#--- if the instrument is different from the original obsid, don't update
#--- the instrument specific parameter values
#
            if ct_dict['instrument'][-1] in ['ACIS-I', 'ACIS-S']:
                excl_list = ['hrc']
            else:
                excl_list = ['acis', 'awin']

            for param in diff_dict.keys():
                if param in rank_list:
                    continue
                else:
                    if diff_dict[param][1] in excl_list:
                        continue

                    ct_dict[param][-1] = diff_dict[param][0]
#
#--- ranked parameters are handled separately
#
            ct_dict = check_ranked_entries('time_ordr',  time_list, oct_dict, ct_dict)

            ct_dict = check_ranked_entries('roll_ordr',  roll_list, oct_dict, ct_dict)

            if ct_dict['instrument'][-1] in ['ACIS-I', 'ACIS-S']:
                ct_dict = check_ranked_entries('aciswin_no', awin_list, oct_dict, ct_dict)
#
#--- create  a dict of: <param> <---> 0:value is updated/1: value is same
#
        ind_dict = csd.create_match_dict(ct_dict)
        chk      = 1
        for param in ind_dict.keys():
            if ind_dict[param]  == 0:
                chk = 0
                break
#
#--- update databases and send out emails
#
        if chk == 0:
            ch_line, out = udrf.update_data_record_file(ct_dict, ind_dict, asis, user)
            for k in range(0, 3):
                note[k] = note[k] + out[k]
        else:
            no_change.append(obsid)


    return note, status, no_change

#-----------------------------------------------------------------------------------------------
#-- check_ranked_entries: update ranked entry values based on the original obsid entries      --
#-----------------------------------------------------------------------------------------------

def check_ranked_entries(gparam, r_list,  oct_dict, ct_dict):
    """
    update ranked entry values based on the original obsid entries
    input:  gparam      --- rank #  of the group
            r_list      --- a list of parameters in that group
            oct_dict    --- a dict of <param> <---> <information> of the original obsid
            ct_dict     --- a dict of <param> <---> <information> of the current obsid
    output  ct_dict     --- an updated data dict
    """
#
#--- check whether the rank # of the new obsid is same as the original obsid before change
#
    same = csd.compare_values(oct_dict[gparam][-2], ct_dict[gparam][-2])
    if same == 1:
#
#--- check whether values in each rank of the current obsid  are same as those of the original
#--- obsid before the updated: ALL PARAMETERS OF ALL RANKS MUST BE SAME in both data sets
#--- to update the ranked values of the new obsid based on the changes in the original obsid
#
        rchk = 0
        for param in r_list:
            for k in range(0, 10):
                same = csd.compare_values(ct_dict[param][-2][k], oct_dict[param][-2][k])
                if same == 0:
                    rchk += 1
#
#--- if all the conditions are met, update the ranked values in the new obsid
#
        if rchk == 0:
            ct_dict[gparam][-1] = oct_dict[gparam][-1]
            for param in r_list:
                ct_dict[param][-1] = oct_dict[param][-1]
#
#--- the original rank is not same, make sure that the original rank is intact in the
#--- 'updated' value
#
    else:
        ct_dict[gparam][-1] = ct_dict[gparam][-2]

    return ct_dict

#-----------------------------------------------------------------------------------------------

if __name__ == '__main__':
    
    submit_other_obsids(obsids_list, oct_dict, asis, user)
