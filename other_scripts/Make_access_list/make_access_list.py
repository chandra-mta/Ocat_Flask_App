#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#################################################################################################
#                                                                                               #
#           make_access_list.py: create an access list for ocatdata2html.cgi                    #
#                                                                                               #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                               #
#               last update: Mar 17, 2021                                                       #
#                                                                                               #
#################################################################################################

import math
import re
import sys
import os
import string
import time
import Chandra.Time
#
#--- reading directory list
#
path = '/data/mta4/CUS/www/Usint/ocat/Info_save/too_dir_list_py3'
with  open(path, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec("%s = %s" %(var, line))
#
#--- append a path to a privte folder to python directory
#
sys.path.append(bin_dir)
sys.path.append(mta_dir)
sys.path.append('/data/mta/Script/Python3.8/Sybase/')

#
#--- mta common functions
#
import mta_common_functions         as mcf
import set_sybase_env_and_run       as sser

#--------------------------------------------------------------------------------------
#-- make_access_list: create an access list for ocatdata2html.cgi                    --
#--------------------------------------------------------------------------------------

def make_access_list():
    """
    create an access list for ocatdata2html.cgi
    input:  none
    output: <obs_ss>/access_list
    """ 
#
#--- get unobserved/schedule list
#
    d_list = []
    cmd = "select obsid, status, type, ocat_propid from target where status='unobserved'"
    out = sser.set_sybase_env_and_run(cmd)

    for ent in out:
        if ent[2] in ['TOO', 'DDT', 'CAL']:
            continue
        else:
            d_list.append(ent)

    cmd = "select obsid, status, type, ocat_propid from target where status='scheduled'"
    out = sser.set_sybase_env_and_run(cmd)

    for ent in out:
        if ent[2] in ['TOO', 'DDT', 'CAL']:
            continue
        else:
            d_list.append(ent)
#
#--- find their pi's and observers
#
    line = ''
    for ent in d_list:
        pid = ent[3]
        cmd = "select last from view_pi where ocat_propid=" + str(pid)
        out = sser.set_sybase_env_and_run(cmd)
        pi  = out[0][0]
    
        cmd = "select last from view_coi where ocat_propid=" + str(pid)
        out = sser.set_sybase_env_and_run(cmd)
        if len(out[0]) == 0:
            co = pi
        else:
            co = out[0][0]

        line = line + str(ent[0]) + '\t' + str(ent[1]) + '\t' + str(ent[3]) + '\t' 
        if len(pi) > 7:
            line = line + pi + ':\t' + co + ':\n'
        elif len(pi) > 3:
            line = line + pi + ':\t\t' + co + ':\n'
        else:
            line = line + pi + ':\t\t\t' + co + ':\n'
#
#--- print out the result
#
    ofile = obs_ss + 'access_list'
    with open(ofile, 'w') as fo:
        fo.write(line)

#--------------------------------------------------------------------------------------

if __name__ == "__main__":

    make_access_list()
