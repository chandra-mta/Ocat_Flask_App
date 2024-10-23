#!/usr/bin/env /proj/sot/ska/bin/python

#################################################################################################################
#                                                                                                               #
#   update_ddt_too_list.py: read sot list and udate ddt_list and too_list                                       #
#                                                                                                               #
#       author: t. isobe (tisobe@cfa.harvard.edu)                                                               #
#                                                                                                               #
#       last update: Mar 02, 2016                                                                               #
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
import mta_common_functions as mcf
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

def update_ddt_too():

    """
    update new_obs_lsit, too_list, ddt_list, and obs_in_30days
    no input but data are taken from sot_ocat.out.

    """
#
#--- set limit to the last 60 days
#
    [year, mon, day, hours, min, sec, weekday, yday, dst] = tcnv.currentTime('LOCAL')
    tdom = tcnv.findDOM(year, mon, day, 0, 0, 0)
    dom_limit = tdom - 60                      
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
#--- read too_list and ddt_list and make obsid <---> poc dictionary
#
    poc_dict = {}
    cddt     = []
    ctoo     = []

    line = too_dir + 'ddt_list'
    fo   = open(line, 'r')
    ddt  = [line.strip() for line in fo.readlines()]
    fo.close()

    for ent in ddt:
        atemp = re.split('\s+', ent)
        obsid = atemp[2].strip()
#
#--- if the poc is 'TBD', skip!
#
        if atemp[4] != 'TBD':
            poc_dict[obsid] = atemp[4] 

        cddt.append(obsid)

    line = too_dir + 'too_list'
    fo   = open(line, 'r')
    too  = [line.strip() for line in fo.readlines()]
    fo.close()

    for ent in too:
        atemp = re.split('\s+', ent)
        obsid = atemp[2].strip()

        if atemp[4] != 'TBD':
             poc_dict[obsid] = atemp[4] 

        ctoo.append(obsid)
    
#
#--- read database
#
    line = obs_ss + 'sot_ocat.out'
    f    = open(line, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()
#
#--- start itelations
#
    fo1     = open('tmp_ddt_list', 'w')
    fo2     = open('tmp_too_list', 'w')
    new_ddt = []
    new_too = []
    for ent in data:
        atemp  = re.split('\^', ent)

        try:
            type   = atemp[14].strip().lower()
            if type != 'too' and type != 'ddt':
                continue

            obsid  = atemp[1].strip()
            seq_no = atemp[3].strip()
            date   = atemp[13].strip()
            if date == 'NULL':
                date   = atemp[15].strip()
            status = atemp[16].strip().lower()
            ao     = atemp[21].strip()
        except:
            continue
#
#--- convert date to dom
#
        if str(date).lower() == 'null' or str(date).lower() == 'none':
            dom = 'NA'
        else:
            temp  = re.split('\s+', str(date))
            omon  = tcnv.changeMonthFormat(temp[0])
            oday  = int(temp[1])
            oyear = int(temp[2])
            dom   = tcnv.findDOM(oyear, omon, oday, 0, 0, 0)

        if status == 'scheduled' or status == 'unobserved' or status == 'observed':

            if status == 'observed':
                if dom == 'NA':
                    continue
                elif dom < dom_limit:
                    continue
            else:
                if dom == 'NA':
                    continue
#
#--- find poc of the observation
#
            try:
#
#--- check this obsid is already assigned poc
#
                person = poc_dict[obsid]
                if person == '':
                    person = 'TBD'
            except:
                person = 'TBD'
#
#--- check this obsid is listed on a special_obsid_poc_list
#
            if person == 'TBD':
                sp_poc = 'na'
                for sval in range(0, len(sp_obsid)):
                    if obsid == sp_obsid[sval]:
                        sp_poc = sp_user[sval]
                        break
#
#-- for the case the obsid is given a specific poc
#
                if sp_poc != 'na':
                    person = sp_poc
#
#--- it is new; so assigned today's poc
#
                else:
                    try:
                        [person, chk]  = tdfnc.find_too_ddt_poc(obsid)
                    except:
                        pass

            line = str(type) + '\t'
            line = line + str(seq_no) + '\t'
            line = line + str(obsid)  + '\t'
            line = line + str(status) + '\t'
            line = line + str(person) + '\t'
            line = line + str(ao)     + '\t'
            line = line + str(date)   + '\n'

            if type == 'ddt':
                fo1.write(line)
                new_ddt.append(obsid)
            else:
                fo2.write(line)
                new_too.append(obsid)

    fo1.close()
    fo2.close()
#
#--- check new one has any entries, if so replace the current one
#
    if len(new_ddt) > 0:
        cmd = 'mv ' + too_dir + 'ddt_list ' + too_dir  + 'ddt_list~'
        os.system(cmd)
        cmd = 'mv tmp_ddt_list ' + too_dir + 'ddt_list'
        os.system(cmd)
        nddt = check_new_entry(cddt, new_ddt)
    else:
        cmd = 'rm tmp_ddt_list'
        os.system(cmd)
        nddt = []

    if len(new_too) > 0:
        cmd = 'mv '+ too_dir + 'too_list ' + too_dir + 'too_list~'
        os.system(cmd)
        cmd = 'mv tmp_too_list ' + too_dir + 'too_list'
        os.system(cmd)
        ntoo = check_new_entry(ctoo, new_too)
    else:
        cmd = 'rm tmp_too_list'
        os.system(cmd)
        ntoo = []
#
#-- if there are new entries, send notification email
#
    if len(nddt) > 0 or len(ntoo) > 0:
        line = 'Possible new entry\n'
        if len(nddt) > 0:
            for obsid in nddt:
                line = line + 'ddt: ' + str(obsid) + '\n'
        if len(ntoo) > 0:
            for obsid in ntoo:
                line = line + 'too: ' + str(obsid) + '\n'

        out = temp_dir + 'mail'
        fo  = open(out, 'w')
        fo.write(line)
        fo.close()

        cmd = 'cat ' + out + ' | mailx -s"Subject: New ddt/too observation" tisobe@cfa.harvard.edu'
        os.system(cmd)

        cmd = 'rm ' + out
        os.system(cmd)

            
                
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------

def check_new_entry(current, new):

    nlist = []
    for ent in new:
        chk = 0
        for comp in current:
            if ent == comp:
                chk = 1
                break
        if chk == 1:
            continue
        else:
            nlist.append(ent)

    return nlist

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


    update_ddt_too()

#    update_from_ddttoo_html()

