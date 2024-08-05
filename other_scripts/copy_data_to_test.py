#!/proj/sot/ska3/flight/bin/python

#########################################################################################
#                                                                                       #
#       copy_data_to_test.py: copying the data to the test directory                    #
#                                                                                       #
#           author: w. aaron (william.aaron@cfa.harvard.edu)                            #
#                                                                                       #
#           last update: Aug 05, 2024                                                   #
#                                                                                       #
#########################################################################################

import os
import re
import numpy

OCAT_DIR = "/data/mta4/CUS/www/Usint/ocat"
COPY_DIR = "/proj/web-cxc/cgi-gen/mta/Obscat/ocat"
#
#--- read the current test data list
#
with open(f'{COPY_DIR}/updates_table.list', 'r') as f:
    data1 = [line.strip() for line in f.readlines()]
#
#--- copy the real data list and approved list
#
os.system(f"cp -f {OCAT_DIR}/updates_table.list {COPY_DIR}/updates_table.list")

os.system(f"cp -f {OCAT_DIR}/approved {COPY_DIR}/approved")
#
#--- read the updated test data list
#
with open(f'{COPY_DIR}/updates_table.list', 'r') as f:
    data2 = [line.strip() for line in f.readlines()]
#
#--- read the list from the previous day
#
if os.path.isfile(f'{COPY_DIR}/comp_list'):
    with open(f'{COPY_DIR}/comp_list', 'r') as f:
        data3 = [line.strip() for line in f.readlines()]
else:
    os.system(f"cp {COPY_DIR}/updates_table.list {COPY_DIR}/comp_list")
    exit(1)
#
#--- compare lists and remove the test data added a day before
#
added = numpy.setdiff1d(data1, data3)

if len(added) > 0:
    for ent in added:
        atemp = re.split('\t+', ent)
        os.system(f"rm -f {COPY_DIR}/updates/{atemp[0]}")
#
#--- compare lists and add the data added in the real database
#
added = numpy.setdiff1d(data2, data3)

if len(added) > 0:
    for ent in added:
        atemp = re.split('\t+', ent)
        os.system(f"cp -fp {OCAT_DIR}/updates/{atemp[0]} {COPY_DIR}/updates/")

    os.system(f"cp -f {COPY_DIR}/updates_table.list {COPY_DIR}/comp_list")

#
#--- Copy Current TOO Schedule
#
os.system(f'cp -f {OCAT_DIR}/Info_save/too_contact_info/schedule  {COPY_DIR}/Info_save/too_contact_info/schedule')

#
#--- Copy cdo_warning_list
#
os.system(f"cp -f {OCAT_DIR}/cdo_warning_list {COPY_DIR}/cdo_warning_list")