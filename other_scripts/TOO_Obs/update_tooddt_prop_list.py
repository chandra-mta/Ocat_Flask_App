#!/usr/bin/env /proj/sot/ska/bin/python

#############################################################################################
#                                                                                           #
#       update_tooddt_prop_list.py: update tooddt_prop_obsid_list/propno_poc_list           #
#                                                                                           #
#       author: t. isobe (tisobe@cfa.harvard.edu)                                           #
#                                                                                           #
#       last update: Apr 05, 2018                                                           #
#                                                                                           #
#############################################################################################

import sys
import os
import string
import re
import getpass

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
#
#--- set a few directory/file paths
#
uspp_dir        = "/proj/web-icxc/htdocs/uspp/TOO/"
outdir          = too_dir + 'tooddt_prop_obsid_list'
tooddt_poc_list = too_dir + 'propno_poc_list'

#---------------------------------------------------------------------------------------------
#-- update_tooddt_prop_list: update tooddt_prop_obsid_list and propno_poc_list              --
#---------------------------------------------------------------------------------------------

def update_tooddt_prop_list():
    """
    update tooddt_prop_obsid_list and propno_poc_list
    input:  none    
    output: tooddt_prop_obsid_list  --- proposal id <---> a list of obsids
            propno_poc_list         --- proposal id <---> poc correpsondace table
    """
#
#--- get prop_poc_dict
#
    propid_poc_dict = find_poc()
#
#--- update too part
#
    prop_list1 = make_too_obs_list()
#
#--- update ddt part
#
    prop_list2 = make_ddt_obs_list()

    prop_list  = prop_list1 + prop_list2
#
#--- read the current prop no <---> poc list
#
    f    = open(tooddt_poc_list, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()
#
#--- drop disappeared (canceled or archived) prop id and add new ones
#
    poc_dict = {}
    for ent in data:
        atemp = re.split('<>', ent)
        poc = atemp[1]
        if poc == 'TBD':
            try:
                poc = propid_poc_dict[atemp[0]]
            except:
                pass
            
        poc_dict[atemp[0]] = poc

    copy = tooddt_poc_list + '~'
    cmd  = 'mv ' + tooddt_poc_list + ' ' + copy
    os.system(cmd)

    fo   = open(tooddt_poc_list, 'w')
    for ent in prop_list:
        try:
            poc = poc_dict[ent]
            line = ent + '<>' + poc + '\n'
        except: 
            line = ent + '<>TBD\n'

        fo.write(line)

    fo.close()
    
#---------------------------------------------------------------------------------------------
#-- make_too_obs_list: create a table of too obsids for corresponding proporsal numbers     --
#---------------------------------------------------------------------------------------------

def make_too_obs_list():
    """
    create a table of too obsids for corresponding proporsal numbers
    input:  none 
    output: <too_dir> + too_prop_obsid_list
            prop_list   --- a list of proposal numbers
    """

    return_prop_list = []
    fo = open(outdir, 'w')
    for cycle in range(13, 100):
        file = uspp_dir + "cycle" + str(cycle) + "_toos.html"
        if mcf.chkFile(file) == 0:
            break

        [prop_list, prop_dict] = find_too_observations(file)

        obsid_status           = find_obsid_status()


        for prop_num in prop_list:
            obsid_list = []
            for obsid in prop_dict[prop_num]:
                try:
                    status = obsid_status[obsid]
                except:
                    status = ''

                if (status == 'archived') or (status == 'canceled'):
                    continue
                else:
                    obsid_list.append(obsid)

            if len(obsid_list) > 0:
                return_prop_list.append(prop_num)
                line = prop_num + '<>' + obsid_list[0]
                for k in range(1, len(obsid_list)):
                    line = line + ':' + obsid_list[k]
                line = line + '\n'
                fo.write(line)
            else:
                continue

    fo.close()

    return return_prop_list

#---------------------------------------------------------------------------------------------
#-- find_too_observations: create lists of too obsids for a corresponding proproal numbers ---
#---------------------------------------------------------------------------------------------

def find_too_observations(file):
    """
    create lists of too obsids for a corresponding proproal numbers
    input:  file        --- a file name
    output: prop_list   --- a list of proposal numbers
            prot_dict   --- a dictionay of a list of obsids for a given proposal number
    """
#
#--- open too lists for a given proposal cycle
#
    f    = open(file, 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    prop_list = []
    prop_dict = {}
    chk1      = 0
    chk2      = 0
    for ent in data:
#
#--- collect all proposal number from the top part of the page
#
        if chk1 == 0:
            mc1 = re.search('<a href="#',  ent)
            if mc1 is not None:
                atemp   = re.split('<a href="#', ent)
                btemp   = re.split('"', atemp[1])
                prop_no = btemp[0]
                prop_list.append(prop_no)
                continue
#
#--- each proposal detail description finishes "End of..."; so look for a new proposal
# 
        mc2 = re.search('End of proposal number', ent)
        if mc2 is not None:
            chk2 = 0
            continue
#
#--- a new proposal detail starts
#
        mc3 = re.search('PROPOSAL NO.' , ent)
        if (mc3 is not None) and (chk2 == 0):
            if chk1 == 0:
                for pname in prop_list:
                    prop_dict[pname] = []
                chk1 = 1
                continue

            atemp   = re.split('PROPOSAL NO.</b>', ent)
            prop_no = atemp[1].strip()
            chk2    = 1
            continue
#
#--- find obsid 
#
        mc4 = re.search('OBSID:',  ent)
        mc5 = re.search('TARGET:', ent)
        if (mc4 is not None) and (mc5 is not None):
            atemp = re.split('OBSID:</b>', ent)
            btemp = re.split('<b>', atemp[1])
            obsid = btemp[0].strip()
#
#--- put in the dictionary
#
            plist = prop_dict[prop_no]
            plist.append(obsid)
            prop_dict[prop_no] = plist
        

    return [prop_list, prop_dict]


#---------------------------------------------------------------------------------------------
#-- find_obsid_status: create a dictionary of obsid <---> status                           ---
#---------------------------------------------------------------------------------------------

def find_obsid_status():
    """
    create a dictionary of obsid <---> status
    input:  none, but the data is read from /data/mta4/obs_ss/sot_ocat.out
    output: obsid_status[obsid] = status
    """

    f    = open('/data/mta4/obs_ss/sot_ocat.out', 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    obsid_status = {}
    for ent in data:
        atemp               = re.split('\^', ent)
        obsid               = atemp[1].strip()
        status              = atemp[16].strip()
        obsid_status[obsid] = status

    return obsid_status


#---------------------------------------------------------------------------------------------
#-- make_ddt_obs_list: a create a table of proposal numbers and obsids related to them      --
#---------------------------------------------------------------------------------------------

def make_ddt_obs_list():
    """
    a create a table of proposal numbers and obsids related to them
    input:  none
    output: updated table of tooddt_prop_obsid_list
            prop_list   --- a list of propsal numbers
    """

    fo = open(outdir, 'a')

    [obsid_list, prop_list] = find_ddt_obsid_status()

    for prop_no in prop_list:

        olist = obsid_list[prop_no]
        if len(olist) > 0:
            olist2 = []
#
#--- just in a case, check the database to see whether there are more than listed in sot data
#
            for obsid in olist:
                olist2.append(obsid)
                monitor = []
                groupid = []
                sqlinfo = tdsql.get_target_info(obsid, monitor, groupid)
                olist2 = olist2 + monitor
                olist2 = olist2 + groupid
#
#--- clean out so that we won't have a duplicated information
#
            olist2.sort()
            olist3 = []
            prev = ''
            for ent in olist2:
                if ent == prev:
                    continue
                else:
                    olist3.append(str(ent))
                    prev = ent

            line = prop_no + '<>' + olist3[0] 
            for k in range(1, len(olist3)):
                line = line + ':' + olist3[k]
            line = line + '\n'
            fo.write(line)

    fo.close()

    return prop_list

#---------------------------------------------------------------------------------------------
#-- find_ddt_obsid_status: find current DDT observaitons and find their proposal numbers    --
#---------------------------------------------------------------------------------------------

def find_ddt_obsid_status():
    """
    find current DDT observaitons and find their proposal numbers
    input: none but read from /data/mta4/obs_ss/sot_ocat.out
    output: obsid_dict  --- a dictionary of a list of obsids for each proposal number
            prop_list   --- a list of proposal numbers
    """

    f    = open('/data/mta4/obs_ss/sot_ocat.out', 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    prop_list  = []
    obsid_dict = {}
    for ent in data:
        mc = re.search('DDT', ent)
        if mc is not  None:
            atemp   = re.split('\^', ent)
            obsid   = int(atemp[1].strip())
            status  = atemp[16].strip()
            prop_no = atemp[19].strip()

            if (status == 'archived') or (status == 'canceled'):
                continue 
#
#--- create a list of obsids and put in the dictionay form 
#
            try:
                alist = obsid_dict[prop_no]
                alist.append(obsid)
                obsid_dict[prop_no] = alist
            except:
                obsid_dict[prop_no] = [obsid]
                prop_list.append(prop_no)

    return [obsid_dict, prop_list]

#---------------------------------------------------------------------------------------------
#-- find_poc: create prop-id <---> poc dictionary from new_obs_list                        ---
#---------------------------------------------------------------------------------------------

def find_poc():
    """
    create prop-id <---> poc dictionary from new_obs_list
    input:  none, but read from tooddt_prop_obsid_list and new_obs_list
    output: propid_poc_dict ---- propid<--->poc dict
    """
    f    = open('/data/mta4/CUS/www/Usint/ocat/approved', 'r')
    app  = [line.strip() for line in f.readlines()]
    f.close()
    spoc = {}
    for ent in app:
        atemp = re.split('\s+', ent)
        spoc[atemp[1]] = atemp[2]

    f    = open('/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/tooddt_prop_obsid_list', 'r')
    prop = [line.strip() for line in f.readlines()]
    f.close()
    
    f    = open('/data/mta4/CUS/www/Usint/ocat/Info_save/too_contact_info/new_obs_list', 'r')
    data = [line.strip() for line in f.readlines()]
    f.close()

    propid_poc_dict = {}
    for ent in data:
        atemp = re.split('\s+', ent)
        if atemp[0] == 'too' or atemp[0] == 'ddt':

            pid = 'NA'
            for comp in prop:
                mc  = re.search(atemp[2], comp)
                if mc is not None:
                    btemp = re.split('<>', comp)
                    pid   = btemp[0]
                    break

            if pid != 'NA':
                poc = atemp[4]
                if poc == 'TBD':
                    try:
                        poc = spoc[atemp[2]]
                    except:
                        pass

                propid_poc_dict[pid] = poc

    return propid_poc_dict
            

#------------------------------------------

if __name__ == '__main__':

    update_tooddt_prop_list()

