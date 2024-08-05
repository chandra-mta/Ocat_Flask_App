#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#########################################################################################
#                                                                                       #
#       copy_data_to_test.py: copying the data to the test directory                    #
#                                                                                       #
#           author: t. isobe (tisobe@cfa.harvard.edu)                                   #
#                                                                                       #
#           last update: Aug 19, 2021                                                   #
#                                                                                       #
#########################################################################################

import sys
import os
import string
import re
import numpy

o_dir = '/data/mta4/CUS/www/Usint/ocat/'
#
#--- read the current test data list
#
with open('./updates_table.list', 'r') as f:
    data1 = [line.strip() for line in f.readlines()]
#
#--- copy the real data list and approved list
#
cmd   = 'cp -f ' + o_dir + 'updates_table.list .'
os.system(cmd)

cmd   = 'cp -f ' + o_dir + 'approved .'
os.system(cmd)
#
#--- read the updated test data list
#
with open('./updates_table.list', 'r') as f:
    data2 = [line.strip() for line in f.readlines()]
#
#--- read the  list from the previous day
#
if os.path.isfile('./comp_list'):
    with open('./comp_list', 'r') as f:
        data3 = [line.strip() for line in f.readlines()]
else:
    cmd = 'cp ./updates_table.list ./comp_list'
    os.system(cmd)
    exit(1)
#
#--- compare lists and remove the test data added a day before
#
added = numpy.setdiff1d(data1, data3)

if len(added) > 0:
    for ent in added:
        atemp = re.split('\t+', ent)
        cmd   = 'rm -f ./updates/' + str(atemp[0]) 
        os.system(cmd)
#
#--- compare lists  add the data added in the real database
#
added = numpy.setdiff1d(data2, data3)

if len(added) > 0:
    for ent in added:
        atemp = re.split('\t+', ent)
        cmd   = 'cp -fp ' + o_dir + 'updates/' + str(atemp[0]) + ' ./updates/.'
        os.system(cmd)

    cmd = 'cp -r ./updates_table.list ./comp_list'
    os.system(cmd)


