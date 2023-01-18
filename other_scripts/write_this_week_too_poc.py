#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#########################################################################################
#													                                    #
#	write_this_week_too_poc.py: write out this week's POC to /data/mta/TOO-POC			#
#													                                    #
#       Note: this script is run by mta, not cus                                        #
#                                                                                       #
#		    author: t. isobe (tisobe@cfa.harvard.edu)	                                #
#													                                    #
#		    last update: Mar 17, 2020								                    #
#													                                    #
#########################################################################################

import sys
import os
import string
import re
#
#--- read POC list
#
ifile = '/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/this_week_person_in_charge'
with open(ifile, 'r')as f:
    data = [line.strip() for line in f.readlines()]
#
#--- exteact an email address of the current POC
#
for ent in data:
    m = re.search('#', ent)
    if m is not None:
        continue

    atemp = re.split('\,', ent)
    email = atemp[-1]
    break
#
#--- write it out
#
with open('/home/mta/TOO-POC', 'w') as fo:
    line = email + '\n'
    fo.write(line)

os.system('chmod 644 /home/mta/TOO-POC')
