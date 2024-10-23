#!/usr/bin/env /proj/sot/ska/bin/python

#####################################################################################################################
#                                                                                                                   #
#   tooddtFunctions.py: a collections of functions used for TOO/DDT list updates                                    #
#                                                                                                                   #
#       author: t. isobe (tisobe@cfa.harvard.edu)                                                                   #
#                                                                                                                   #
#       last update: Dec 11, 2014                                                                                   #
#                                                                                                                   #
#####################################################################################################################

import sys
import os
import string
import re
import getpass

#
#--- reading directory list
#

#path = '/proj/web-cxc/cgi-gen/mta/Obscat/ocat/Info_save/dir_list_new'           #---- test directory list path
#path = '/data/mta4/CUS/www/Usint/TOO_Obs/dir_list'
#path = '/data/udoc1/ocat/Info_save/too_dir_list_py'                                #---- live directory list path
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



#---------------------------------------------------------------------------------------------
#--- removeDuplicate: remove duplicated entries from a list                                ---
#---------------------------------------------------------------------------------------------

def removeDuplicate(seq, sorted='NA'):

    'remove duplicated entries froma list and optionally sort the list. input: list,  sorted="NA" '

    outset = []

    if len(seq) > 0:
        cleaned = list(set(seq))
        if sorted == 'NA':
            for ent in cleaned:
                outset.append(ent)
    
        else:
            cleaned.sort()
            for ent in  cleaned:
                outset.append(ent)

    return outset


#---------------------------------------------------------------------------------------------
#--- find_person_in_charge: find who is POC today                                          ---
#---------------------------------------------------------------------------------------------

def find_person_in_charge(target, grating):

    """
    find who is POC today. input: target and grating to handle special case

    """

    line = too_dir + 'this_week_person_in_charge'
    f    = open(line, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    for ent in data:

        m = re.search('\#', ent)

        if m is None:
            atemp    = re.split('\,', ent)
            poc_mail = atemp[4]
            line = too_dir + 'personal_list'
            f     = open(line, 'r')
            plist = [line.strip() for line in f.readlines()]
            f.close()

            person_in_charge = 'TBD'

            for person in plist:
                n = re.search(poc_mail, person)
                if n is not None:
                    btemp = re.split('\<\>', person)
                    ctemp = re.split('\@',   btemp[4])
                    person_in_charge = ctemp[0]

                    if person_in_charge == 'pzhao':
                        person_in_charge = 'ping'
                    elif person_in_charge == 'swolk':
                        person_in_charge = 'sjw'
                    elif person_in_charge == 'nadams':
                        person_in_charge = 'nraw'
                    elif person_in_charge == 'jdrake':
                        person_in_charge = 'jd'

#
#--- special cases
#
    if target.lower() == 'crab':
        person_in_charge = 'ppp'
    elif target.lower() == 'jupiter' or target.lower() == 'saturn':
        person_in_charge = 'sjw'
    elif grating.lower() == 'letg' or grating.lower() == 'hetg':
        person_in_charge = grating.lower()

    return person_in_charge

#------------------------------------------------------------------------------------------------------
#--- find_current_poc: find who are currently assigned poc for approved too/ddt observations         --
#------------------------------------------------------------------------------------------------------

def find_current_poc():

    """
    find who are currently assigned poc for approved too/ddt observations
    output: dict form of obsid, poc pair

    """

    obsid_poc_dict = {}

#
#--- new_obs_list
#
    line = too_dir + 'new_obs_list'
    f    = open(line, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    for ent in data:
        atemp = re.split('\s+|\t+', ent)
        if atemp[0].lower() == 'ddt' or atemp[0].lower() == 'too':
            obsid_poc_dict[int(atemp[2])] = atemp[4]

#
#--- monitor_too_ddt
#
    monitor_dict = read_monitor_too_ddt()

    for key in monitor_dict:
        obsid_poc_dict[key] = monitor_dict[key]

#
#--- ddt_list
#
    try:
        line = too_dir + 'ddt_list'
        f    = open(line, 'r')
        data = [line.strip() for line in f.readlines()]
        f.close()
    
        for ent in data:
            atemp = re.split('\s+|\t+', ent)
            obsid_poc_dict[int(atemp[2])] = atemp[4]
    except:
        pass
#
#--- too_list
#
    try:
        line = too_dir + 'too_list'
        f    = open(line, 'r')
        data = [line.strip() for line in f.readlines()]
        f.close()

        for ent in data:
            atemp = re.split('\s+|\t+', ent)
            obsid_poc_dict[int(atemp[2])] = atemp[4]
    except:
        pass

    return obsid_poc_dict


#---------------------------------------------------------------------------------------------
#--  match_usint_person: find usint person who is in charge for the observation            ---
#---------------------------------------------------------------------------------------------

def match_usint_person(type, grating, seq, instrument, target):

    """
    find usint person who is in charge for the observation.
    input, tpye, grating, sequence #, instrument
    """

    if type.lower() == 'cal':
        poc = 'cal'
    elif grating.lower() == 'letg':
        poc = 'letg'
    elif grating.lower() == 'hetg':
        poc = 'hetg'
    elif instrument.lower() == 'hrc':
        poc = 'hrc'
    elif seq >= 100000 and seq < 300000:
        poc = 'sjw'
    elif seq >= 300000 and seq <390000:
	poc = 'sjw'
    elif seq >= 400000 and seq <490000:
	poc = 'sjw'
#    elif seq >= 300000 and seq < 500000:
#        poc = 'nraw'
    elif seq >= 500000 and seq < 600000:
        poc = 'jeanconn'
    elif seq >= 600000 and seq < 700000:
        poc = 'ping'
    elif seq >= 700000 and seq < 800000:
        poc = 'brad'
    elif seq >= 800000 and seq < 900000:
        poc = 'ping'
    elif seq >= 900000 and seq < 1000000:
        poc = 'das'

#
#--- special cases
#
    if target.lower() == 'crab':
        poc = 'ppp'
    elif target.lower() == 'jupiter' or target.lower() == 'saturn':
        poc = 'sjw'
    elif grating.lower() == 'letg' or grating.lower() == 'hetg':
        poc = grating.lower()

    return poc

#---------------------------------------------------------------------------------------------
#--- find_obs_date: find the observation date for a given obsid                             --
#---------------------------------------------------------------------------------------------

def find_obs_date(obsid):

    """
    find the observation date for a given obsid.

    """
#
#---checking the current user
#
    user = getpass.getuser()
    user = user.strip()

    if user == 'mta':
        cmd = 'lynx -source http://acis.mit.edu/cgi-bin/get-obsid?id=' + str(obsid) + ' > ' + mtemp_dir + 'ztemp'
    elif user == 'cus':
        cmd = 'lynx -source http://acis.mit.edu/cgi-bin/get-obsid?id=' + str(obsid) + ' > ' + ctemp_dir + 'ztemp'
    else:
        print "the user is not mta or cus. Exiting"
        eixt(1)

    os.system(cmd)

    line = mtemp_dir + 'ztemp'
    f    = open(line, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    cmd = 'rm ' + mtemp_dir + 'ztemp'
    os.system(cmd)

    chk = 0
    for ent in data:
        if chk == 1:
            atemp = re.split('\<tt\>', ent)
            btemp = re.split('\<',     atemp[1])
            date  = btemp[0]
            chk += 1
            break
        else:
            m = re.search('Start Date:', ent)
            if m is not None:
                chk = 1

    atemp = re.split('\s+|\t+', date)
    btemp = re.split('-',       atemp[0])

    mon = tcnv.changeMonthFormat(int(btemp[1]))         #--- convert digit month to letter month

#
#--- change time format from 24 hr to 12 hr system
#
    ctemp = re.split(':',  atemp[1])
    part = 'AM'
    time  = int(ctemp[0])
    if time >= 12:
        time -= 12
        part = 'PM'

    stime = str(time)
    if time < 10:
        stime = '0' + stime

    stime = stime + ':' + ctemp[1] + part
    date  = mon + ' ' + btemp[2] + ' ' + btemp[0] + ' ' + stime
    
    return date


#------------------------------------------------------------------------------------------------------
#-- read_too_ddt_html: read all approved ddt and too entries from ddttoo.html page                  ---
#------------------------------------------------------------------------------------------------------

def read_too_ddt_html(ddtList, tooList):

    """
    read all approved ddt and too entries. The lists are returned as ddtList and tooList
    html address: https://icxc.harvard.edu/mp/html/ddttoo.html

    """


#
#--- https://icxc.harvard.edu/mp/html/ddttoo.html gives the list of approved ddt and too observations
#

    f   = open('/proj/web-icxc/htdocs/mp/html/ddttoo.html', 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    ddt_list = []
    too_list = []

    for ent in data:
        m1 = re.search('<h4>Unobserved/Pending DDT Observations:', ent)
        m2 = re.search('<h4>Unobserved/Pending TOO Observations:', ent)
        m3 = re.search('asc.harvard.edu/cgi-gen/target_param.cgi', ent)
        m4 = re.search('Approved?',       ent)
        m5 = re.search('<!-- status -->', ent)

        if m1 is not None:
            type = 'ddt'
        elif m2 is not None:
            type = 'too'
        elif m3 is not None:
            atemp = re.split('\?', ent)
            btemp = re.split('\'', atemp[1])
            obsid = int(btemp[0])
        elif m4 is not None:
            m6 = re.search('Y', ent)
            if m6 is not None:
                app = 1
            else:
                app = 0
        elif m5 is not None:
            if app == 1:
                m7 = re.search('observed',   ent)
                m8 = re.search('scheduled',  ent)
                m9 = re.search('unobserved', ent)
                if (m7 is not None) or (m8 is not None) or (m9 is not None):
		    try:
		    	mtest = int(obsid)
                    	if type == 'ddt':
                            if obsid < 100000 and obsid > 0:
                               ddt_list.append(obsid)
                               app   = -1
                               obsid =  0
	
                    	elif type == 'too':
                       	    if obsid < 100000 and obsid > 0:
                                too_list.append(obsid)
                                app   = -1
                                obsid =  0
		    except:
		        pass

#
#--- pass to the outside of the world
#
    for ent in ddt_list:
        chk = check_obs_status(ent)
        if chk == 1:
            ddtList.append(ent)

    ddtList.sort()

    for ent in too_list:
        chk = check_obs_status(ent)
        if chk == 1:
            tooList.append(ent)

    tooList.sort()

#------------------------------------------------------------------------------------------------------
#--- check_obs_status: check obsid is eligible to add to the current list                           ---
#------------------------------------------------------------------------------------------------------

def check_obs_status(obsid):

    """
    check obsid is eligible to be added to the curren list. 
    input: obsid. if it is either 'scheduled', 'unobserved', or 'observed' status and if it is obsverd
    less than 30 day ago, it is eliible. 
    """
#
#--- set limit to the last 30  days
#
    [year, mon, day, hours, min, sec, weekday, yday, dst] = tcnv.currentTime('LOCAL')
    tdom = tcnv.findDOM(year, mon, day, 0, 0, 0)
    dom_limit = tdom - 30

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
    if chk  == 1:
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
    
            if dom  > dom_limst:
                chk = 1
            else:
                chk = 0
    
        else:
            chk = 0

    return chk


#------------------------------------------------------------------------------------------------------
#--- read_sot_ocat_ddt_too: extract ddt/too shceduled/undnobserved obsids from sot_ocat.out         ---
#------------------------------------------------------------------------------------------------------

def read_sot_ocat_ddt_too(ddtList, tooList):

    """
    extract ddt/too shceduled/unobserved obsids from sot_ocat.out 
    The lists are returned as ddtList and tooList

    """

    ddt_list = []
    too_list = []

    line = obs_ss + 'sot_ocat.out'
    f    = open(line, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    for ent in data:
        m1 = re.search('DDT', ent)
        m2 = re.search('TOO', ent)

        if m1 is not None:
            m3 = re.search('scheduled',  ent)
            m4 = re.search('unobserved', ent)
            if (m3 is not None) or (m4 is not None):
                atemp = re.split('\^', ent)
                ddt_list.append(int(atemp[1]))
        elif m2 is not None:
            m3 = re.search('scheduled',  ent)
            m4 = re.search('unobserved', ent)
            if (m3 is not None) or (m4 is not None):
                atemp = re.split('\^', ent)
                too_list.append(int(atemp[1]))

#
#--- pass to the outside of the world
#
    for ent in ddt_list:
        ddtList.append(ent)

    ddtList.sort()

    for ent in too_list:
        tooList.append(ent)

    tooList.sort()

#------------------------------------------------------------------------------------------------------
#--- find_new_entry: compare two lists and find unique entries from the first list                  ---
#------------------------------------------------------------------------------------------------------

def find_new_entry(new_list, old_list):

    """
    compare two lists and find unique entries from the first list
    input : new_list, old_list
    output: new_entry: list which contains unique entries from first_list

    """

    f   = open(new_list, 'r')
    new = [line.strip() for line in f.readlines()]
    f.close()

    new_obsid = []
    for ent in new:
        atemp = re.split('\s+|\t+', ent) 
        new_obsid.append(atemp[2].strip())


    f   = open(old_list, 'r')
    old = [line.strip() for line in f.readlines()]
    f.close()

    old_obsid = []
    for ent in old:
        atemp = re.split('\s+|\t+', ent)
        old_obsid.append(atemp[2].strip())


    new_list = list(set(new_obsid).difference(set(old_obsid)))

    new_entry = []
    if len(new_list) > 0:
        for i in range(0, len(new_obsid)):
            for comp in new_list:
                if new_obsid[i] == comp:
                    new_entry.append(new[i])

    return new_entry

#------------------------------------------------------------------------------------------------------
#-- send_email: send email notice to poc                                                            ---
#------------------------------------------------------------------------------------------------------

def send_email(type, list, tempdir='NA'):

    """
    send email notice to poc 
    input: type (too, ddt, etc), list: e.g.: 'too     501726  14141   unobserved      das     Dec 13 2012 12:00AM'
           tempdir: if it is given, use that directoy, if not the current directory
    """

    if tempdir == 'NA':
        tempdir = './'

    tempfile = tempdir + 'ztemp'

    if type != 'too' and type != 'ddt':
        f = open(tempfile, 'w')
        for ent in list:
            line = ent + '\n'
            f.write(line)
        f.close()

#
#--- send out email to notify completion of backup
#
        cmd = 'cat ' + tempfile + ' | mailx -s"Subject: New Observations" isobe@head.cfa.harvard.edu'
        os.system(cmd)

        cmd = 'rm ' + tempfile
        os.system(cmd)

    else:
        for ent in list:
            atemp = re.split('\s+|\t+', ent)
            email = findemail(atemp[4])
            obsid = atemp[2]

            f = open(tempfile, 'w')
            line  = '\nA new ' + type.upper() + ' observation (OBSID: ' + obsid + ') is assigned to you. Please check:\n\n'
            f.write(line)
            line =  'https://cxc.cfa.harvard.edu/mta/CUS/Usint/ocatdata2html.cgi?' + obsid + '\n\n'
            f.write(line)
            line = 'for more information.\n\n'
            f.write(line)
            line = 'If this you are not the final support astronomer for this observations, \n'
            f.write(line)
            line = 'please reply to isobe@cfa.harvard.edu cc:cus@cfa.harvard.edu.\n'
            f.write(line)
            f.close()

            subject = 'Subject: New ' + type.upper() + ' Observation (' + email + ')'
            cmd = 'cat ' + tempfile + ' | mailx -s"' + subject + '" isobe@head.cfa.harvard.edu'
            os.system(cmd)

            subject = 'Subject: New ' + type.upper() + ' Observation '
##            cmd = 'cat ' + tempfile + ' | mailx -s"' + subject + '"  ' + email + ' -c"swolk@head.cfa.harvard.edu cus@cfa.harvard.edu" ' 
##            os.system(cmd)

            cmd = 'rm ' + tempfile
            os.system(cmd)

#------------------------------------------------------------------------------------------------------
#-- findemail: find email address of a given poc                                                    ---
#------------------------------------------------------------------------------------------------------

def findemail(poc):

    """
    find email address of a given poc. Input poc name. 
    """

    line = too_dir + 'usint_personal'
    f    = open(line, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    email = 'NA'

    for ent in data:
        atemp = re.split(':', ent)
        if atemp[0] == poc:
            email = atemp[5].strip()
            break

    return email

#------------------------------------------------------------------------------------------------------
#--- read_monitor_too_ddt: read existing monitor_too_ddt list                                        --
#------------------------------------------------------------------------------------------------------

def read_monitor_too_ddt():

    """
    read existing monitor_too_ddt list. output is obsid/poc pair dict.
    """

    line = too_dir + 'monitor_too_ddt'
    f    = open(line, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    monitor_dict = {}
    for ent in data:
        atemp = re.split('\s+|\t+', ent)
        monitor_dict[int(atemp[0])] = atemp[1]

    return monitor_dict


#------------------------------------------------------------------------------------------------------
#--- update_monitor_list: update monitor_too_ddt                                                     --
#------------------------------------------------------------------------------------------------------

def update_monitor_list(new_ddt_too_list, new_ddt_too_person, tempdir='NA'):

    """
    update monitor_too_ddt. input: lists of: new_ddt_too_list and new_ddt_too_person (obsid list and poc list)

    """
#
#--- read the current monitor_too_ddt list
#
    line = too_dir + 'monitor_too_ddt'
    f    = open(line, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

#
#--- three information we need; obsid, who is poc, and proposal id which is same for all obsids in the same monitor/group
#
    added_obsid  = []
    added_person = []
    added_propid = []

    for ent in data:
        atemp = re.split('\s+|\t+', ent)
        obsid = int(atemp[0].strip())
#
#--- get the basic information about the observations and update the current data
#
        monitor = []
        groupid = []
        sqlinfo = tdsql.get_target_info(obsid, monitor, groupid)
        try:
            chk = 1
#            (group_id, pre_id, pre_min_lead, pre_max_lead, grating, type, instrument, obs_ao_str, status, \
#            seq_nbr, ocat_propid, soe_st_sched_date, lts_lt_plan,targname)

            status = sqlinfo[8]
            ocat_propid = sqlinfo[10]

            if status == 'observed' or status == 'scheduled' or status == 'unobserved':
                line = str(obsid) + '\t' + atemp[1] + '\t' + str(ocat_propid)
                added_obsid.append(obsid)
                added_person.append(atemp[1])
                added_propid.append(ocat_propid)
        except:
            pass

#
#--- now check the new obsids are totally new or one of group/monintor members
#
    for i in range(0, len(new_ddt_too_list)):

        nobsid = int(new_ddt_too_list[i])
        chk = 0
        for comp in added_obsid:
            if comp == nobsid:
                chk = 1

        if chk == 0:
            monitor = []
            groupid = []
            try:
                chk = 1
                (group_id, pre_id, pre_min_lead, pre_max_lead, grating, type, instrument, obs_ao_str, status, \
                seq_nbr, ocat_propid, soe_st_sched_date, lts_lt_plan,targname) = tdsql.get_target_info(nobsid, monitor,groupid)

                if len(monitor) > 0:
                    for ment in monitor:
                        added_obsid.append(int(ment))
                        added_person.append(new_ddt_too_person[i])
                        added_propid.append(int(ocat_propid))

                if len(group) > 0:
                    for gent in group:
                        added_obsid.append(int(gent))
                        added_person.append(new_ddt_too_person[i])
                        added_propid.append(int(ocat_propid))

            except:
                pass

#
#--- make a list with neede information
#
    if len(added_obsid) > 0:
        updated_list = []
        for i in range(0, len(added_obsid)):
            line = str(added_obsid[i]) + '\t' + added_person[i] + '\t' + str(added_propid[i])
            updated_list.append(line)

        updated_list.sort()
#
#--- save the old list
#
        cmd = 'mv ' + too_dir + 'monitor_too_ddt ' + too_dir + 'monitor_too_ddt~'
        os.system(cmd)
    
        line = too_dir + 'monitor_too_ddt'
        out = open(line, 'w')
        for ent in updated_list:
            out.write(ent)
            out.write('\n')
    
        out.close()
#
#--- check whether there are any new entries
#

        new_file = too_dir + 'monitor_too_ddt'
        old_file = too_dir + 'monitor_too_ddt~'
        newentry = find_new_entry(new_file, old_file)
        if len(newentry) > 0:

            if tempdir == 'NA':
                tempdir = './'
        
            tempfile = tempdir + 'ztemp'
        
            f = open(tempfile, 'w')
            line = 'Following obsids are added to monitor_too_ddt list. Please check whether they are correct.\n\n'
            f.write(line)

            for ent in newentry:
                line = ent + '\n'
                f.write(line)

            f.close()

            cmd = 'cat ' + tempfile + ' | mailx -s"Subject: New Monitor Entry" tisobe@cfa.harvard.edu'
            os.system(cmd)


#---------------------------------------------------------------------------------------------
#-- update_list: update list for a given obsid list                                        ---
#---------------------------------------------------------------------------------------------

def update_list(list_name, newList):

    """
    update list for a given obsid list.
    input: list_name (e.g., too_list, ddt_list), newList: a list of new obsids

    """

#
#--- save the old file
#

    old = list_name + '~'
    cmd = 'cp ' + too_dir + list_name + ' '+ too_dir + old
    os.system(cmd)

#
#--- open an appropriate list (too_list or ddt_list, but can be new_obs_list)
#

    line = too_dir + list_name
    f    = open(line, 'a')

    emailList       = []
    new_obsid_list  = []
    new_person_list = []

    for obsid in newList:
        monitor = []
        group   = []
#
#--- read basic information about the observation
#
        try:
            (group_id, pre_id, pre_min_lead, pre_max_lead, grating, type, instrument, obs_ao_str, status, seq_nbr, \
             ocat_propid, soe_st_sched_date, lts_lt_plan,targname) = tdsql.get_target_info(obsid, monitor, group)
            chk = 1
        except:
            chk = 0

#
#--- if there are information available, procceed
#
        if chk > 0:
#
#--- check whether obsid is already in monitor_list, and have assigned poc
#--- if not, find who is the charge for the observation
#
            obsid_poc_dict = find_current_poc()
            try:
                poc = obsid_poc_dict[obsid]
            except:
                poc = find_person_in_charge(targname, grating)

#
#--- set observation date; probably soe_st_sched_date, but if not lts_lt_plan 
#
            if str(soe_st_sched_date).lower() != 'null' and str(soe_st_sched_date).lower() != 'none':
                date = soe_st_sched_date
            else:
                date = lts_lt_plan

#
#--- append the new observation to the list
#
            line = type.lower() + '\t' + str(seq_nbr) + '\t' + str(obsid) + '\t' + status + '\t' + poc + '\t' + str(date) + '\n'
            f.write(line)
            emailList.append(line)
            new_obsid_list.append(obsid)
            new_person_list.append(poc)

    f.close()

#
#--- check monitor_list and update if necessary
#
    update_monitor_list(new_obsid_list, new_person_list)

#
#--- notify the update by email
#
    atemp = re.split('_', list_name)
    send_email(atemp[0], emailList, temp_dir)

#---------------------------------------------------------------------------------------------
#-- read_current_obsid: create obsid list from given table                                 ---
#---------------------------------------------------------------------------------------------

def read_current_obsid(list_name):

    """
    read obsid from the list. input file name
    """

    clist = []
    try:
        f    = open(list_name, 'r')
        data = [line.strip() for line in f.readlines()]
        f.close()
    
    
        for ent in data:
            atemp = re.split('\s+|\t+', ent)
            clist.append(int(atemp[2]))

    except:
        pass

    return clist


#------------------------------------------------------------------------------------------------------------------
#-- comp_two_record_lists: compare two lists and extract data with obsids only in the first list                ---
#------------------------------------------------------------------------------------------------------------------

def comp_two_record_lists(list1, list2):

    """
    compare two lists and extract data with obsids only in the first list
    input: two lists such as too_list and too_list~
    """

    f     = open(list1, 'r')
    data1 = [line.strip() for line in f.readlines()]
    f.close()
    obsidList1 = []
    for ent in data1:
        atemp = re.split('\s+|\t+', ent)
	try:
       	    obsidList1.append(atemp[2])
	except:
            pass

    f     = open(list2, 'r')
    data2 = [line.strip() for line in f.readlines()]
    f.close()
    obsidList2 = []
    for ent in data2:
        atemp = re.split('\s+|\t+', ent)
	try:
            obsidList2.append(atemp[2])
        except:
            pass

    newobsids  = list(set(obsidList1).difference(set(obsidList2)))

    newentry   = pick_lines(data1, newobsids)

    return newentry

#------------------------------------------------------------------------------------------------------------------
#--- pick_lines: choose line from list with entries of tag list                                                 ---
#------------------------------------------------------------------------------------------------------------------

def pick_lines(list, tags):

    """
    choose lines from a list with entries in tag list
    input: list example: too_list, tags: obsid list
    """

    newentry = []
    for ent in list:
        atemp = re.split('\s+|\t+', ent)
        for comp in tags:
            if str(atemp[2]) == str(comp):
                newentry.append(ent)

    return newentry


#
#---- added Dec 11, 2014 ----
#


#---------------------------------------------------------------------------------------------
#-- find_too_ddt_poc: find a poc for a give obsid specifically for too or ddt              ---
#---------------------------------------------------------------------------------------------

def find_too_ddt_poc(obsid):
    """
    find a poc for a give obsid specifically for too or ddt
    input:  obsid       --- obsid
    output: [poc,chk]   --- poc and status. 0 if poc is already assigned, 1 if it is new
    """
#
#--- convert obsid to string as the dictionay take only a string
#
    obsid = str(obsid)
    file = too_dir + 'new_obs_list'
    f    = open(file, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()
#
#--- create obsid - poc dictionary from the existing data
#
    poc_dict = {}
    for ent in data:
        atemp = re.split('\s+', ent)
        if atemp[0] == 'too' or atemp[0] == 'ddt':
            poc_dict[atemp[2]] = atemp[4]

    try:
#
#--- for the case obsid is already in the existing list
#
        poc = poc_dict[obsid]
        if poc == 'TBD':
            poc = find_too_ddt_poc_sub(obsid)
            return [poc, 1]
        else:
            return [poc, 0]
    except:
#
#--- for the case obsid is not in the existing list
#
            poc = find_too_ddt_poc_sub(obsid)
            return [poc, 1]

#---------------------------------------------------------------------------------------------
#-- find_too_ddt_poc_sub: find poc from obsid by reading tables.                            --
#---------------------------------------------------------------------------------------------

def find_too_ddt_poc_sub(obsid):
    """
    find poc from obsid by reading tables. 
    input:  obsid   --- obsid
    output: poc     --- poc

    """
    try:
#
#--- get the basic information about the observations and update the current data
#
        monitor = []
        groupid = []
        sqlinfo = tdsql.get_target_info(obsid, monitor, groupid)
        grating = sqlinfo[4]
        prop_no = sqlinfo[10]
        target  = sqlinfo[13]

        poc = find_poc_from_propno_poc_list(prop_no)
    except:
#
#--- if the database is not set up for the obsid, try to another method
#
        poc = check_tooddt_prop_obsid_list(obsid)

    return poc

#---------------------------------------------------------------------------------------------
#-- find_poc_from_propno_poc_list: find a poc from a proposal number using propno_poc_list  --
#---------------------------------------------------------------------------------------------

def find_poc_from_propno_poc_list(prop_no):
    """
    find a poc from a proposal number using propno_poc_list
    input:  prop_no     --- proposal number
    output: poc         --- poc
    """
    file = too_dir + 'propno_poc_list'
    f    = open(file, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    poc = 'TBD'
    for ent in data:
        atemp = re.split('<>', ent)
        if prop_no == atemp[0]:
            poc = atemp[1]
            break
#
#--- if poc is not listed in the table, assign today's poc
#
    if poc == 'TBD':
        poc = find_person_in_charge(target, grating)

    return poc

#---------------------------------------------------------------------------------------------
#-- check_tooddt_prop_obsid_list: check intooddt_prop_obsid_list and poc                   ---
#---------------------------------------------------------------------------------------------

def check_tooddt_prop_obsid_list(obsid):
    """
    check whether obsid is listed intooddt_prop_obsid_list and find poc from there
    input:  obsid   --- obsid
    output: poc     --- poc
    """

    file = too_dir + 'tooddt_prop_obsid_list'
    f    = open(file, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()
#
#--- find proposal # corresponding to obsid
#
    prop_no = 'na'
    for ent in data:
        mc = re.search(obsid, ent)
        if mc is not None:
            atemp = re.split('<>', ent)
            prop_no = atemp[0]
            break;
    if prop_no == 'na':
        poc = 'TBD'
    else:
#
#--- if it finds a correspointing proposal #, try to find poc from it
#
        poc = find_poc_from_epropno_poc_list(prop_no)

    return poc
    

#-------------------------------------------------------------------------------


if __name__ == "__main__":

#    obsid_poc_dict = find_current_poc()
#
#    for key in obsid_poc_dict:
#        print str(key) + ' : '  + obsid_poc_dict[key]

    """
    obs_list =[14141]
    person_list=['das']
    update_monitor_list(obs_list, person_list)
    """

