#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#################################################################################
#                                                                               #
#       check_unobserved_obsids.py: check obsid with unobserved status          #
#                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                           #
#                                                                               #
#           last update: Sep 21, 2021                                           #
#                                                                               #
#################################################################################

import os
import sys
import re
import string
import random
import time
import Chandra.Time

#
#--- temp writing file name
#
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)
#
#--- file names
#
ufile  = '/data/mta4/CUS/www/Usint/ocat/house_keeping/Unobserved/unobserved_list'
cfile  = '/data/mta4/obs_ss/sot_ocat.out'

cus    = 'cus@cfa.harvard.edu'
admin  = 'bwargelin@cfa.harvard.edu'
tech   = 'lina.pulgarin-duque@cfa.harvard.edu'

#---------------------------------------------------------------------------
#-- check_unobserved: check obsid with unobserved status and send out email 
#---------------------------------------------------------------------------

def check_unobserved():
    """
    check obsid with unobserved status and send out email
    input:  none but read from /data/mta4/obs_ss/sot_ocat.out
    output: ./unobserved_list   --- a list of unobserved obsids
            email sent out. if there are new unobserved obsid, or
                            obsids with status unobservered sitting
                            more than 3 months, email will be sent out.
    """
#
#--- set today's time in seconds from 1998.1.1
#
    today = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
    today = int(Chandra.Time.DateTime(today).secs)
#
#--- read the past unobserved obsid list
#
    with open(ufile, 'r') as f:
        data = [line.strip() for line in f.readlines()]
    pobsid_list = []
    time_dict   = {}
    for ent in data:
        atemp = re.split(':', ent)
        obsid = atemp[0].strip()
        pobsid_list.append(obsid)
        time_dict[obsid] = int(float(atemp[-1]))
#
#--- read the current unobserved obsid list
#
    cobsid_list = []
    c_dict      = {}
    aline = ''
    with open(cfile, 'r') as f:
        data = [line.strip() for line in f.readlines()]

    for ent in data:
        mc = re.search('unobserved', ent)
        if mc is None:
            continue

        atemp  = re.split('\^', ent)
        obsid  = atemp[1].strip()
        seq_no = atemp[2].strip()
        inst   = atemp[12].strip()
        otype  = atemp[14].strip()
        lts    = atemp[15].strip()

        if lts != 'NULL':
            continue
        if otype in ['TOO', 'DDT']:
            continue

        cobsid_list.append(obsid)
        line          = obsid + ':' + seq_no + ':' + inst
        c_dict[obsid] = line
        try:
            stime = time_dict[obsid]
            aline = aline + line + ':' + str(stime) + '\n'
        except:
            aline = aline + line + ':' + str(today) + '\n'
#
#--- update the unobserved_list
#
    with open(ufile, 'w') as fo:
        fo.write(aline)
#
#--- find new unobserved obsids
#
    new_obsids = list(set(cobsid_list) - set(pobsid_list))
#
#--- find obsids older than 3 months ago
#
    old_obsids = []
    for obsid in cobsid_list:
        try:
            otime = time_dict[obsid]
            tdiff = today - otime
            if tdiff > 86400 * 90:
                old_obsids.append(obsid)
        except:
            continue
#
#--- if there are obsids older than 3 months send out email
#
    chk   = 0
    eline = ''
    if len(old_obsids) > 0:
        eline = eline + 'Following observations are in "unobserved" status for more than 3 months '
        eline = eline + 'without assigned LTS time:\n\n'
        eline = eline + 'Obsid  :  SeqNo  :  Inst\n'
        eline = eline + '-------------------------\n'
        for ent in old_obsids:
            eline = eline + c_dict[ent].replace(':', '  :  ') + '\n'
        chk = 1
#
#--- if there are new unobserved obsids, send out email
#            
    if len(new_obsids) > 0:
        eline = eline + '\n\n'
        eline = eline + '==========================\n'
        eline = eline + '\n\n'
        eline = eline + 'Following observations appeared as "unobserved" this week:\n\n'
        eline = eline + 'Obsid  :  SeqNo  :  Inst\n'
        eline = eline + '-------------------------\n'
        for ent in new_obsids:
            eline = eline + c_dict[obsid].replace(':', '  :  ') + '\n'
        chk = 1

    if chk > 0:
        with open(zspace, 'w') as fo:
            fo.write(eline)

        cmd = 'cat ' + zspace + '|mailx -s"Unobserved Obsids Notification" '
        cmd = cmd  + ' -b ' + tech + ' -c ' + cus +  ' ' + admin 
        os.system(cmd)

        cmd = 'rm -rf ' + zspace
        os.system(cmd)

#---------------------------------------------------------------------------

if __name__ == '__main__':
    check_unobserved()
