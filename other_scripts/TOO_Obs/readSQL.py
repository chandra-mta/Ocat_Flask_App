#!/usr/bin/env /proj/sot/ska/bin/python

#####################################################################################################
#                                                                                                   #
#   readSQL.py: read data from sql database.                                                        #
#                                                                                                   #
#       author: t. isobe (tisobe@cfa.harvard.edu)                                                   #
#                                                                                                   #
#       last update: Apr 05, 2018                                                                   #
#                                                                                                   #
#####################################################################################################

#--- if above does  not work, use /proj/sot/ska/bin/python with Ska.DBI (below)
#--- from Ska.DBI import *

import sys
import os
import string
import re

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
#--- append path to a privte folder
#

sys.path.append(bin_dir)
sys.path.append(mta_dir)

import convertTimeFormat as tcnv
#
#--- sybase module
#

from DBI import *

#----------------------------------------------------------------------------------------------------------------
#-- readSQL: or a given sql command and database, return result in dictionary form                            ---
#----------------------------------------------------------------------------------------------------------------

def readSQL(cmd, database):

    """
    for a given sql command and database, return result in dictionary form.

    """

    #db_user = 'browser'
    #line    = pass_dir + '.targpass'
    #server  = 'sqlxtest'
    #line    = pass_dir + '.targpass_itest'

    db_user = 'mtaops_internal_web'
    server  = 'ocatsqlsrv'

    line      = pass_dir + '.targpass_internal'
    f         = open(line, 'r')
    db_passwd = f.readline().strip()
    f.close()

    db = DBI(dbi='sybase', server=server, user=db_user, passwd=db_passwd, database=database)

    outdata = db.fetchone(cmd)

    return outdata


#----------------------------------------------------------------------------------------------------------------
#--- get_target_info: extract a basic target information for a given obsid                                    ---
#----------------------------------------------------------------------------------------------------------------

def get_target_info(obsid, monitor, group):

    """
    extract a basic target information for a given obsid. mintor and group obsids are in list form.

    """

    database = 'axafocat'

    cmd = 'select group_id,pre_id,pre_min_lead,pre_max_lead,grating,type,instrument,obs_ao_str,status,seq_nbr,ocat_propid,soe_st_sched_date,lts_lt_plan,targname,object from target where obsid=' + str(obsid)

    targetdata   = readSQL(cmd, database)

    group_id          = targetdata['group_id']
    pre_id            = targetdata['pre_id']
    pre_min_lead      = targetdata['pre_min_lead']
    pre_max_lead      = targetdata['pre_max_lead']
    grating           = targetdata['grating']
    type              = targetdata['type']
    instrument        = targetdata['instrument']
    obs_ao_str        = targetdata['obs_ao_str']
    status            = targetdata['status']
    seq_nbr           = targetdata['seq_nbr']
    ocat_propid       = targetdata['ocat_propid']
    soe_st_sched_date = targetdata['soe_st_sched_date']
    lts_lt_plan       = targetdata['lts_lt_plan']
    targname          = targetdata['targname']
    object            = targetdata['object']

    monitor_flag = 'N'
    if pre_id:
        monitor_flag = 'Y'

    cmd = 'select distinct pre_id from target where pre_id=' + str(obsid)
    out  = readSQL(cmd, database)
    try:
    	pre_id_match = out['pre_id']
    	if pre_id_match is not None:
        	monitor_flag = 'Y'
    except:
	pass

#
#--- check group entries
#
    if group_id is not None:
        monitor_flag = 'N'
        pre_min_lead = 'None'
        pre_max_lead = 'None'
        pre_id       = 'None'

        cmd = 'select obsid from target where group_id=' + group_id

        out = readSQL(cmd, database)
        for ent in out:
	    val = ent['obsid']
	    group.append(val)


#
#--- if monitor flag is Y, find which obsids blong to this monitor list
#
    if monitor_flag == 'Y':
        monitor_add  = find_monitor_obs(obsid)

        for ent in monitor_add:
            monitor.append(ent)

#
#--- update ao #
#
    cmd = 'select ao_str from prop_info where ocat_propid=' + str(ocat_propid)
    out = readSQL(cmd, database)
    obs_ao_str = out['ao_str']

    return (group_id, pre_id, pre_min_lead, pre_max_lead, grating, type, instrument, obs_ao_str, status, seq_nbr, ocat_propid, soe_st_sched_date, lts_lt_plan,targname, object)


#----------------------------------------------------------------------------------------------------------------
#--- find_monitor_obs: find obsid on a monitor list                                                           ---
#----------------------------------------------------------------------------------------------------------------

def find_monitor_obs(obsid):

    """
    for a given obsid, check all other obsid on the same monitor list. return monitor_list.

    """
    database = 'axafocat'

#    db_user = 'browser'
#    server  = 'ocatsqlsrv'
#
#    line      = pass_dir + '.targpass'
#    f         = open(line, 'r')
#    db_passwd = f.readline().strip()
#    f.close()
#    database  = 'axafocat'
#
#    db = DBI(dbi='sybase', server=server, user=db_user, passwd=db_passwd, database=database)

    db_user = 'mtaops_internal_web'
    server  = 'ocatsqlsrv'

    line      = pass_dir + '.targpass_internal'
    f         = open(line, 'r')
    db_passwd = f.readline().strip()
    f.close()

    db = DBI(dbi='sybase', server=server, user=db_user, passwd=db_passwd, database=database)

    #outdata = db.fetchone(cmd)

    monitor_list = [obsid]
    series_rev(obsid, db, monitor_list)
    series_fwd(obsid, db, monitor_list)

    monitor_list = removeDuplicate(monitor_list, sorted="Yes")


    return monitor_list
    
#----------------------------------------------------------------------------------------------------------------
#---  series_rev: extract a series of pre-id for a given obsid                                                ---
#----------------------------------------------------------------------------------------------------------------

def series_rev(obsid, db, monitor):

    """
    for given obsid, database, and monitor list, exract series of pre-id realated to obsid. return monitor_list
    this one checks obsid in decreasing manner.

    """
    chk = 0
    cmd =  'select obsid from target where pre_id=' + str(obsid)
    try:
        for row in db.fetch(cmd):
            obs = row['obsid']
            if obs == '':
                chk = 1
            else:
                if str(obs).isdigit():
                    monitor.append(obs)
                    if chk == 0:
                        series_rev(obs, db, monitor)
                else:
                    break
    except:
        pass

#----------------------------------------------------------------------------------------------------------------
#--- series_fwd: extract a series of pre-id for a given obsid. this one look forward.                         ---
#----------------------------------------------------------------------------------------------------------------

def series_fwd(obsid, db, monitor):

    """
    for given obsid, database, and monitor list, exract series of pre-id realated to obsid. return monitor_list
    this one checks obsid in increase manner.
    
    """

    monitor = []
    chk = 0
    cmd =  'select pre_id from target where obsid=' + str(obsid)
    try:
        for row in db.fetch(cmd):
            obs = row['pre_id']
            if obs == '':
                chk = 1
            else:
                if str(obs).isdigit():
                    monitor.append(obs)
                    if chk == 0:
                        series_fwd(obs, db, monitor)
                else:
                    break

    except:
        pass

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

if __name__ == '__main__':

    """
    olist = find_monitor_obs(14225)    

    for ent in olist:
        print ent

    """

    monitor = []
    group   = []
    obsid   = 14141
    target = get_target_info(obsid, monitor, group)

    for ent in target:
        print str(ent)

    if len(group) > 0:
        print "group id"
        for ent in group:
            print ent

    if len(monitor) > 0:
        print "monitor"
        for ent in monitor:
            print ent


