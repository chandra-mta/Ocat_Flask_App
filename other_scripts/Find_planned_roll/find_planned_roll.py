#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#################################################################################################
#                                                                                               #
#       find_planned_roll.py: extract obsid and planned roll angle from MP site                 #
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
#
#--- mta common functions
#
import mta_common_functions         as mcf

#--------------------------------------------------------------------------------------
#-- find_planned_roll: read planned roll angles from MP long term web page           --
#--------------------------------------------------------------------------------------

def find_planned_roll():
    """
    read planned roll angles from MP long term web page
    input:  none, but read from /proj/web-icxc/htdocs/mp/lts/lts-current.html
    output: <obs_id>/mp_long_term
    """
#
#--- read MP long term web page
    ifile = '/proj/web-icxc/htdocs/mp/lts/lts-current.html'
    data  = mcf.read_data_file(ifile)

    line  = ''
    for ent in data:
        mc = re.search('LTS changes', ent)
        if mc is not None:
            break

        mc = re.search('target_param\.cgi', ent)
        if mc is not None:
#
#--- find obsid
#
            atemp = re.split('target_param\.cgi\?', ent)
            btemp = re.split('\"', atemp[1])
            obsid = int(float(btemp[0]))
#
#--- find planned role
#
            atemp = re.split('\s+', ent)
            acnt  = 0
            for val in atemp:
                mc1 = re.search('ACIS', val)
                mc2 = re.search('HRC',  val)
                if (mc1 is not None) or (mc2 is not None):
                    break
                else:
                    acnt += 1

            if acnt > 0:
                pl_roll   = atemp[acnt-4]
                pl_range  = atemp[acnt-3]

                line = line + str(obsid) + ':' + str(pl_roll) + ':' + str(pl_range) + '\n'

        ofile = obs_ss + 'mp_long_term'
        with open(ofile, 'w') as fo:
            fo.write(line)


#--------------------------------------------------------------------------------------

if __name__ == "__main__":

    find_planned_roll()
