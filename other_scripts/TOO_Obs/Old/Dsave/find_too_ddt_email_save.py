#!/usr/bin/env /proj/sot/ska/bin/python

#################################################################################################################
#                                                                                                               #
#   find_too_ddt_email.py: find newly approved ddt and/or too observations and update ddt_list and too_list     #
#                                                                                                               #
#           author: t. isobe (tisobe@cfa.harvard.edu)                                                           #
#                                                                                                               #
#           last update: Mar 26, 2013                                                                           #
#                                                                                                               #
#################################################################################################################


import sys
import os
import string
import re
import getpass

#
#--- reading directory list
#

#path = '/proj/web-cxc/cgi-gen/mta/Obscat/ocat/Info_save/dir_list_new'           #---- test directory list path
#path = '/data/mta4/CUS/www/Usint/TOO_Obs/too_dir_list'                                #---- live directory list path
#path = '/data/udoc1/ocat/Info_save/too_dir_list_py'
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

import readSQL         as tdsql
import tooddtFunctions as tdfnc

#
#--- check who is the user, and set a path to Log location
#
user = getpass.getuser()
user = user.strip()
if user == 'mta':
    temp_dir = mtemp_dir
elif user == 'cus':
    temp_dir = ctemp_dir
elif user == 'html':
    temp_dir = htemp_dir
else:
    temp_dir = './'


#-----------------------------------------------------------------------------------------------------
#-- read_ddt_too_from_email: extreact TOO/DDT obsid from cus email archive                         ---
#-----------------------------------------------------------------------------------------------------

def read_ddt_too_from_email(tooList, ddtList):

    """
    extreact TOO/DDT obsid from cus email achive. no input, but need tooList, ddtList.
    """

#
#--- read email archive
#
    f    = open('/arc/cus/mail_archive', 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

#
#--- find certain signatures for TOO/DDT observation approved email, and extract their obsids
#

    tooSet = []
    ddtSet = []
    tchk = 0
    dchk = 0
    for ent in data:

        m1 = re.search('Obsid', ent)

        if m1 is not None: 
            m2 = re.search('Seq',   ent)
            m5 = re.search('Prop',  ent)

            if m2 is not None: 

#                m3 = re.search('is a TOO which has recently', ent)
#                m4 = re.search('is a DDT which has recently', ent)
                m3 = re.search('is a TOO',   ent)
                m4 = re.search('is a DDT',   ent)

                if m3 is not None:
                    obsid = getObsid(ent)
                    tooSet.append(obsid)
                    tchk += 1

                elif m4 is not None:
                    obsid = getObsid(ent)
                    ddtSet.append(obsid)
                    dchk += 1

            elif m5 is not None: 

                m6 = re.search('is a TOO',   ent)
                m7 = re.search('is a DDT',   ent)

                if m6 is not None:
                    obsid = getObsid(ent)
                    tooSet.append(obsid)
                    tchk += 1

                elif m7 is not None:
                    obsid = getObsid(ent)
                    ddtSet.append(obsid)
                    dchk += 1
            
#
#---- remove duplicated entries
#

    tlen = 0
    dlen = 0
    if tchk > 0:
        tempList = tdfnc.removeDuplicate(tooSet, sorted='yes')
        tlen    = len(tempList)
        if tlen > 0:
            for ent in tempList:
                monitor = []
                group   = []
                sqlinfo = tdsql.get_target_info(ent, monitor, group)
                status  = sqlinfo[8]
                if status == 'unobserved':
                    tooList.append(ent)


    if dchk > 0:
        tempList = tdfnc.removeDuplicate(ddtSet, sorted='yes')
        dlen    = len(tempList)
        if dlen > 0:
            for ent in tempList:
                monitor = []
                group   = []
                sqlinfo = tdsql.get_target_info(ent, monitor, group)
                status  = sqlinfo[8]
                if status == 'unobserved':
                    ddtList.append(ent)

    return tlen + dlen


#---------------------------------------------------------------------------------------------
#--- getObsid: extract obsid from the line --- works only TOO/DDT email notification       ---
#---------------------------------------------------------------------------------------------

def getObsid(line):

    'extract obsid from the line --- works only TOO/DDT email notification, input: line'

    atemp = re.split('Obsid', line)
    btemp = re.split('\(',    atemp[1])
    obsid = int(btemp[0])
    return obsid


#---------------------------------------------------------------------------------------------
#-- update_too_ddt_from_email: find approved obsid from email and update too/ddt lists -------
#---------------------------------------------------------------------------------------------

def update_too_ddt_from_email():

    """
    find approved obsid from email and update too/ddt lists.
    no input, but read from email achive. update too_dr/too_list and ddt_list

    """

#
#--- read existing TOO/DDT observations
#
    line = too_dir + 'too_list'
    tooObsid = tdfnc.read_current_obsid(line)
    line = too_dir + 'ddt_list'
    ddtObsid = tdfnc.read_current_obsid(line)

#
#--- read email and find whether any notificaiton of new DDT/TOO observations available
#

    tooList = []
    ddtList = []
    tooNew  = []
    ddtNew  = []

    chk = read_ddt_too_from_email(tooList, ddtList)         #--- function to pick up obsid from email archive

    if chk == 0:
        return 0

    else:
#
#--- extract only totally new Obsids
#
        if len(tooList) > 0:
            tooNew = list(set(tooList).difference(set(tooObsid)))

        if len(ddtList) > 0:
            ddtNew = list(set(ddtList).difference(set(ddtObsid)))

#
#--- if there are actually new obsids, update lists
#
    if len(ddtNew) > 0:
            tdfnc.update_list('ddt_list', ddtNew)
    if len(tooNew) > 0:
            tdfnc.update_list('too_list', tooNew)



#---------------------------------------------------------------------------------------------

if __name__ == '__main__':

    update_too_ddt_from_email()

#    cmd = 'chgrp mtagroup ' + too_dir + '* '
#    os.system(cmd)
