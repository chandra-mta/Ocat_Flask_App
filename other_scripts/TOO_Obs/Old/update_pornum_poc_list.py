#!/usr/bin/env /proj/sot/ska/bin/python

#############################################################################################
#                                                                                           #
#       update_pornum_poc_list.py: update propno_poc_list                                   #
#                                                                                           #
#           author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                           #
#           last update: Mar 02, 2016                                                       # 
#                                                                                           #
#############################################################################################

import sys
import os
import string
import re

#
#--- reading directory list
#

path = '/data/mta4/CUS/www/Usint/ocat/Info_save/too_dir_list_py'

f    = open(path, 'r')
data = [line.strip() for line in f.readlines()]
f.close()

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec "%s = %s" %(var, line)
#
#--- append path to a private folder
#
sys.path.append(bin_dir)
sys.path.append(mta_dir)

import mta_common_functions as mcf
import convertTimeFormat    as tcnv
import readSQL              as tdsql

#---------------------------------------------------------------------------------------------
#-- find_poc_for_propnum: update propno_poc_list                                            --
#---------------------------------------------------------------------------------------------

def find_poc_for_propnum():
    """
    update propno_poc_list
    input:  none
    output: udated propno_poc_list
    """
#
#--- create obsid <---> poc dictionary
#
    f    = open('/data/mta4/CUS/www/Usint/ocat/approved', 'r')
    data = [line.strip() for line  in f.readlines()]
    f.close()

    app_poc = {}
    for ent in data:
        atemp = re.split('\s+', ent)
        app_poc[atemp[0]] = atemp[2]
#
#--- create prop num <---> poc dictionary
#
    f    = open('/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/tooddt_prop_obsid_list', 'r')
    data = [line.strip() for line  in f.readlines()]
    f.close()

    prop_poc = {}
    for ent in data:
        atemp = re.split('<>', ent)
        olist = re.split(':', atemp[1])

        poc = 'TBD'
        for obsid in olist:
            try:
                poc = app_poc[obsid]
                break
            except:
                pass
            
        prop_poc[atemp[0]] = poc
#
#---- update propno_poc_list 
#
    f    = open('/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/propno_poc_list', 'r')
    data = [line.strip() for line  in f.readlines()]
    f.close()

    for ent in data:
        atemp = re.split('<>', ent)
        if atemp[1] == 'TBD':
            try:
                poc = prop_poc[atemp[0]]
            except:
                poc = 'TBD'
        else:
            poc = atemp[1]

        print atemp[0] + '<>' + poc

#---------------------------------------------------------------------------------------

if __name__ == '__main__':

    find_poc_for_propnum()
