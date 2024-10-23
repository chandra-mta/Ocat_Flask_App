#!/usr/bin/env /proj/sot/ska/bin/python

#################################################################################################################
#                                                                                                               #
#   update_new_obs_list.py: read sot list and udate new_obs_ist, too_list, ddt_list, and obs_in_30days          #
#                                                                                                               #
#       author: t. isobe (tisobe@cfa.harvard.edu)                                                               #
#                                                                                                               #
#       last update: Oct 26, 2012                                                                               #
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
#path = '/data/mta4/CUS/www/Usint/TOO_Obs/dir_list';
path = '/data/udoc1/ocat/Info_save/too_dir_list_py'                                #---- live directory list path
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

import convertTimeFormat as tcnv
import tooddtFunctions   as tdfnc
import readSQL           as sql

#
#--- check whose account, and set a path to temp location
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


#------------------------------------------------------------------------------------------------------
#--- update_new_obs_list: update, new_obs_list                                                      ---
#------------------------------------------------------------------------------------------------------

def update_new_obs_list():

    """
    update new_obs_lsit, too_list, ddt_list, and obs_in_30days
    no input but data are taken from sot_ocat.out.

    """

#
#--- set limit to the last 30  days
#
    [year, mon, day, hours, min, sec, weekday, yday, dst] = tcnv.currentTime('LOCAL')
    tdom = tcnv.findDOM(year, mon, day, 0, 0, 0)
    dom_limit = tdom - 30                      
    dom30days = tdom + 30                           #---- use to find observations will happen in 30 days
#
#--- read currently assigned ddt/too pocs; save as dict form
#

    obsid_poc_dict = tdfnc.find_current_poc()

#
#--- read special obsid --- poc list
#
    line = too_dir + 'special_obsid_poc_list'
    f    = open(line, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()
    sp_obsid = []
    sp_user  = []
    for ent in data:
        atemp = re.split('\s+', ent)
        sp_obsid.append(atemp[0])
        sp_user.append(atemp[1])

#
#--- read database
#
    line = obs_ss + 'sot_ocat.out'
    f    = open(line, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    out_list = []

#
#--- open temporary writing files
#
    line = temp_dir + 'new_obs_list'
    out1 = open(line, 'w')
    line = temp_dir + 'too_list'
    out2 = open(line, 'w')
    line = temp_dir + 'ddt_list'
    out3 = open(line, 'w')
    line = temp_dir + 'obs_in_30days'
    out4 = open(line, 'w')
#
#--- these two are used to update monitor list
#
    new_ddt_too_list   = []
    new_ddt_too_person = []

#
#--- start itelations
#
    for ent in data:
        atemp   = re.split('\^', ent)
        status  = atemp[16].strip().lower()
        date    = atemp[13].strip()
#
#--- limit data re-checking to the last 30 days
#
        if str(date).lower() == 'null' or str(date).lower() == 'none':
            dom = 'NA'
        else:
            temp  = re.split('\s+', str(date))
            omon  = tcnv.changeMonthFormat(temp[0])
            oday  = int(temp[1])
            oyear = int(temp[2])
            dom   = tcnv.findDOM(oyear, omon, oday, 0, 0, 0)

        ochk = 0
        if str(date).lower() == 'null' or str(date).lower() == 'none':
            ochk = 1
        else:

            if dom > dom_limit:
                ochk = 1

        if ochk ==1  and (status == 'scheduled' or status == 'unobserved' or status == 'observed'):
            chk   = 0
            obsid = atemp[1].strip()
#
#--- check this obsid is listed on a special_obsid_poc_list
#
            sp_poc = 'na'
	    for sval in range(0, len(sp_obsid)):
		if obsid == sp_obsid[sval]:
		    sp_poc = sp_user[sval]
		    break

#
#--- extract basic information
#
            monitor = []
            groupid = []
            try:
                (group_id, pre_id, pre_min_lead, pre_max_lead, grating, type, instrument, obs_ao_str, status, \
                seq_nbr, ocat_propid, soe_st_sched_date, lts_lt_plan,targname) = sql.get_target_info(int(obsid), monitor,groupid)

                if soe_st_sched_date is not None:
                    date = soe_st_sched_date
                    chk = 1
                elif lts_lt_plan is not None:
                    date = lts_lt_plan
                    chk  = 1
                else:
                    date = 'NA'
                    chk = 0
            except:
                date = 'NA'
                chk = 0
#
#--- check status change
#
            if status == 'scheduled' or status == 'unobserved' or status == 'observed':
#
#--- recompute with updated date
#
                if date == 'NA':
                    dom = 'NA'
                else:
                    temp  = re.split('\s+', str(date))
                    omon  = tcnv.changeMonthFormat(temp[0])
                    oday  = int(temp[1])
                    oyear = int(temp[2])
                    dom   = tcnv.findDOM(oyear, omon, oday, 0, 0, 0)

#
#--- if it is ddt or  too, add to the list anyway
#
                if type.lower() == 'ddt' or type.lower() == 'too':
                    chk = 1
                    if date == 'NA':
                        dom = tdom + 1000
#
#--- the observation is cleared all criteria;  prepare to print them out to files
#
                if chk == 1:
    
                    pchk = 1
		    if sp_poc != 'na':
#
#-- for the case the obsid is given a specific poc
#
			person = sp_poc

                    elif type.lower() == 'ddt' or type.lower() == 'too':
#
#-- too/ddt case: assign poc
#
                        if date == 'NA':
                            person = 'TBD'
                        else:
                            try:
                                person = obsid_poc_dict[int(obsid)]
                            except:
                                person = 'TBD'
#
#--- observed obsid but no poc name -- record mistake; so drop
#
                            if person  == 'TBD':
                                if status == 'observed':
                                    pchk = 0
                                else:
                                    person = tdfnc.find_person_in_charge(targname, grating)
                                    new_ddt_too_list.append(int(obsid))
                                    new_ddt_too_person.append(person)
                    else:
#
#--- none too/ddt observations
#
                        person = tdfnc.match_usint_person(type,grating,int(seq_nbr),instrument, targname)
    
#
#--- print out to files
#
                    if pchk == 1:
                        line  = type.lower() + '\t' + str(seq_nbr) + '\t' + obsid + '\t' + status  + '\t' + person + '\t' + str(obs_ao_str) + '\t' + str(date) + '\n'
                        if person != 'TBD' and type.lower() == 'too':
                            out2.write(line)
                        elif person != 'TBD' and type.lower() == 'ddt':
                            out3.write(line)

                        out1.write(line)

                        if status != 'observed' and dom < dom30days:
                            out4.write(line)

    out1.close()
    out2.close()
    out3.close()
    out4.close()

    completeTask(temp_dir, too_dir, 'too_list')
    completeTask(temp_dir, too_dir, 'ddt_list')
    completeTask(temp_dir, too_dir, 'new_obs_list')
    completeTask(temp_dir, too_dir, 'obs_in_30days')

#
#---- create new_obs_list.txt
#
    ofile = too_dir + 'new_obs_list.txt'
    out   = open(ofile, 'w')
    out.write('Type    Seq #   ObsId   Status          TOO     AO      Observation Date\n')
    out.write('--------------------------------------------------------------------------\n\n')
    out.close()
    cmd = 'cat ' + too_dir + 'new_obs_list >> ' + ofile
    os.system(cmd)


#------------------------------------------------------------------------------------------------------
#-- completeTask: mv a list to a proper location, and send out email if there is new obsid           --
#------------------------------------------------------------------------------------------------------

def completeTask(temp_dir, outdir, lname):

    """
    mv a list to a proper location, and send out email if there is new obsid  
    input: temp_dir: a dir where a file is created
           outdir:  a dir where the files are kept, usually too_dir
           lname:   a file name, e.g., too_list, ddt_list, new_obs_list, and obs_in_30days
    """

#
#--- change the old file name to that with "~"
#
    oname = lname + '~'
    cmd = 'mv ' + outdir + lname + ' ' + outdir +  oname
    os.system(cmd)

#
#--- move the new one to the too_dir
#
    cmd = 'mv ' + temp_dir + lname + ' ' + outdir + lname
    os.system(cmd)

#
#--- check whether there are any new observations. if so, send out notification email
#
    lname2  = outdir + lname
    oname2  = outdir + oname
    new_ent = tdfnc.comp_two_record_lists(lname2, oname2)

    if len(new_ent) > 0 and lname != 'obs_in_30days':
        atemp = re.split('_list', lname)
        tdfnc.send_email(atemp[0], new_ent)


#------------------------------------------------------------------------------------------------------
#-- update_from_ddttoo_html: update too/ddt list based on ddttoo.html entries                       ---
#------------------------------------------------------------------------------------------------------

def update_from_ddttoo_html():

    """
    update too/ddt list based on ddttoo.html entries
    no input, but use ddttoo.html and current ddt_list and too_list
    """

#
#--- read obsids currently listed ddtoo.html as active
#

    ddtList = []
    tooList = []

    tdfnc.read_too_ddt_html(ddtList, tooList)

#
#--- read obsid currently listed on ddt_list and too_list
#
    line = too_dir + 'ddt_list'
    ddtCurrent = tdfnc.read_current_obsid(line)
    line = too_dir + 'too_list'
    tooCurrent = tdfnc.read_current_obsid(line)

#
#--- compare and select out obsids only listed in ddttoo.html
#

    ddt_new_entry = list(set(ddtList).difference(set(ddtCurrent)))
    too_new_entry = list(set(tooList).difference(set(tooCurrent)))

#
#--- update ddt_list and too_list
#

    if len(ddt_new_entry) > 0:
        tdfnc.update_list('ddt_list', ddt_new_entry)

    if len(too_new_entry) > 0:
        tdfnc.update_list('too_list', too_new_entry)


#---------------------------------------------------------------------------------------------

if __name__ == "__main__":


    update_new_obs_list()

    update_from_ddttoo_html()

    cmd = 'chgrp mtagroup ' + too_dir + '* '
    os.system(cmd)

