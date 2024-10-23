#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#############################################################################################
#                                                                                           #
#       check_hrc_si_mode_sign_off.py: check hrc si mode sign off status                    #
#                                                                                           #
#           author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                           #
#           last update: Sep 21, 2021                                                       #
#                                                                                           #
#############################################################################################

import os
import sys
import re
import string
import random
import math
import time

rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)

email = 'dpatnaude@cfa.harvard.edu,grant.tremblay@cfa.harvard.edu,pnulsen@cfa.harvard.edu'

#------------------------------------------------------------------------------
#-- check_hrc_si_status: check hrc si mode sign off status and send out email if it is required
#------------------------------------------------------------------------------

def check_hrc_si_status():
    """
    check hrc si mode sign off status and send out email if it is required
    input:  none, but read from update_table.list
    output: email sent out for warning
    """
#
#--- create obsid <--> instrument dictionary
#
    ifile  = '/data/mta4/obs_ss/sot_ocat.out'
    data   = read_data_file(ifile)
    o_dict = {}
    for ent in data:
        atemp = re.split('\^', ent)
        obsid = int(float(atemp[1].strip()))
        inst  = atemp[12].strip()
        o_dict[obsid] = inst
#
#--- read obsid status list and find out which HRC observations are not signoff yet
#
    ifile = '/data/mta4/CUS/www/Usint/ocat/updates_table.list'
    data  = read_data_file(ifile)

    warning = []
    for ent in data:
        atemp = re.split('\t+', ent)
        if len(atemp) < 8:
            continue
#
#--- check the observation is already signed off
#
        if atemp[5] != 'NA':
            continue
        btemp = re.split('\.', atemp[0])
        obsid = int(float(btemp[0]))
        try:
            inst = o_dict[obsid]
        except:
            continue
#
#--- if it is HRC observation, check si mode signoff status
#
        mc = re.search('HRC', inst)
        if mc is not None:
            if atemp[4] == 'NA':
                warning.append(atemp[0])
#
#--- if there are hrc si mode which are not signed offm, send out warning email
#
    if len(warning) > 0:
        line = 'Following obsid/rev are still waiting for HRC SI Mode approval\n\n'
        for ent in warning:
            line = line + ent + '\n'

        line = line + '\nPlease go to \n'
        line = line + 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi'
        line = line + '\n and sign off it as soon as possible.\n'

        with open(zspace, 'w') as fo:
            fo.write(line)

        cmd = 'cat ' + zspace + ' | mailx -s"HRC SI Mode Sign Off Request" ' + email
        os.system(cmd)

        cmd = 'cat ' + zspace + ' | mailx -s"HRC SI Mode Sign Off Request" lina.pulgarin-duque@cfa.harvard.edu'
        os.system(cmd)

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def read_data_file(ifile):

    with open(ifile, 'r') as f:
        data = [line.strip() for line  in f.readlines()]

    return data

#------------------------------------------------------------------------------

if __name__ == "__main__":

    check_hrc_si_status()
