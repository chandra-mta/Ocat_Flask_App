#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#################################################################################################
#                                                                                               #
#   find_mismatch.py:  check update_table.list and check whether a phantom entry is created     #
#                                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                                           #
#                                                                                               #
#           last update: Sep 21, 2021                                                           #
#                                                                                               #
#################################################################################################

import math
import re
import sys
import os
import string
import numpy
import time
import random
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
#
#--- cus common functions
#
import cus_common_functions         as ccf
#
#--- temp writing file name
#
import random
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)
#
#--- tech email address
#
tech  = 'lina.pulgarin-duque@cfa.harvard.edu'

#-----------------------------------------------------------------------------------------------------
#---find_mismatch: check update_table.list and check whether a phantom entry is created in the list --
#-----------------------------------------------------------------------------------------------------

def find_mismatch():
    """
    this script reads /data/mta4/CUS/www/Usint/ocat/updates_table.list and compares files 
    created in /data/mta4/CUS/www/Usint/ocat/updates/ if there are any mismatchs, the script 
    reports the fact to tech.
    input:  no
    output: email to tech, update saved_file (past mismatched list)
    """
#
#--- read the past mismatch entries
#
    mfile     = house_keeping + 'Mismatch/mismatch_list'
    data      = ccf.read_data_file(mfile)
    past_list = []
    for ent in data:
        try:
            val = float(ent)
            past_list.append(val)
        except:
            pass
    past_list = sorted(past_list)
#
#--- read names of files in the data directry
#
    cmd = 'ls /data/mta4/CUS/www/Usint/ocat/updates/* > ' + zspace
    os.system(cmd)
    
    data = ccf.read_data_file(zspace, remove=1)

    file_list = []
    for ent in data:
        atemp =  re.split('\/', ent)
        try:
            val = float(atemp[-1])
            file_list.append(val)
        except:
            pass

    file_list = sorted(file_list)
#
#---- read the names on the list
#
    ifile = '/data/mta4/CUS/www/Usint/ocat/updates_table.list'
    data  = ccf.read_data_file(ifile)

    entry_list =[]
    for ent in data:
        atemp = re.split('\s+', ent)
        try:
            val = float(atemp[0])
            entry_list.append(float(atemp[0]))
        except:
            pass

    entry_list = sorted(entry_list)
#
#--- find mismatches between the name in the list and the files in the data directory
#
    diff       = numpy.setdiff1d(entry_list, file_list)
#
#--- check whether there are new mismatch data
#
    new_list   = numpy.setdiff1d(diff, past_list)
#
#--- if there are, report and update the mismatch list
# 
    if len(new_list) > 0:
        line = ''
        for ent in new_list:
            line  = line + str(ent) + '\n'

        with open(mfile, 'a') as fo:
            fo.write(line)

        with open(zspace, 'w') as fo:
            fo.write(line)
        
        cmd = 'cat '+ zspace + '| mailx -s "Subject: Mismatch in updates_table.list" ' + tech 
        os.system(cmd)

        ccf.rm_files(zspace)

#---------------------------------------------------------------------

if __name__ == '__main__':
    
    find_mismatch()


