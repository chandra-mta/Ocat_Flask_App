#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#################################################################################################
#                                                                                               #
#           find_scheduled_obs.py: find MP scheduled observations                               #
#                                                                                               #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                               #
#               last update: Mar 17, 2021                                                       #
#                                                                                               #
#################################################################################################

import math
import re
import sys
import os
import string
import time
import Chandra.Time
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
sys.path.append(mta_dir)
sys.path.append('/data/mta/Script/Python3.8/Sybase/')
#
#--- mta common functions
#
import mta_common_functions         as mcf
import set_sybase_env_and_run       as sser
#
#--- temp writing file name
#
import random
rtail    = int(time.time() * random.random())
zspace   = '/tmp/zspace' + str(rtail)
#
#--- a character list to be used
#
chr_list = list('ABCDEFG')

#--------------------------------------------------------------------------------------
#-- find_scheduled_obs: find MP scheduled observations                               --
#--------------------------------------------------------------------------------------

def find_scheduled_obs():
    """
    find MP scheduled observations
    input:  none but read from /data/mpcrit1/mplogs/* directory
    ouptput <obs_ss>/scheduled_obs_list
    """
#
#--- find today's date
#
    out = time.strftime('%Y:%m:%d', time.gmtime())
    atemp = re.split(':', out)
    year  = int(float(atemp[0]))
    mon   = int(float(atemp[1]))
    mday  = int(float(atemp[2]))
    umon  = mcf.change_month_format(mon).upper()
    lmon  = mcf.change_month_format(mon).lower()
#
#--- next month
#
    nyear = year
    nmon  = mon + 1
    if mon > 12:
        nyear += 1
        nmon   = 1
    unmon = mcf.change_month_format(nmon).upper()
    lnmon = mcf.change_month_format(nmon).lower()
#
#--- find all MP OR lists scheduled to start after today
#
    cmd = 'ls -rtd /data/mpcrit1/mplogs/' + str(year)  + '/' + umon  + '* > '  + zspace
    os.system(cmd)

    d_list = mcf.read_data_file(zspace, remove=1)
#
#--- find direcotries hold data after today's date
#--- the directory name: <MMM><dd><yy>, e.g. JUL2020
#
    n_list = []
    for ent in d_list:
        atemp = re.split(umon, ent)
        date  = atemp[1][0] + atemp[1][1]
        date  = int(float(date))
        if date > mday:
            n_list.append(ent)
#
#--- find all *.or files and mp persons responsible for that schedule
#
    [f_list, u_list] = find_file_and_mp(n_list)
#
#--- check the next month, if directory exists
#
    cmd = 'ls /data/mpcrit1/mplogs/' + str(nyear) + '> ' +  zspace
    os.system(cmd)

    with open(zspace, 'r') as f:
        test = f.read()
    mcf.rm_files(zspace)

    mc  = re.search(unmon, test)
    if mc is not None:
        cmd = 'ls -rltd /data/mpcrit1/mplogs/' + str(nyear) + '/' + unmon + '* >> ' + zspace
        os.system(cmd)
        d_list = mcf.read_data_file(zspace, remove=1)

        [f_list2, u_list2] = find_file_and_mp(d_list, nchk=1)

        f_list = f_list + f_list2
        u_list = u_list + u_list2
#
#--- get all observations under schedules
#
    m_list = []                 #--- a list of obsids
    o_dict = {}                 #--- a dictionary to keep info related obsids
    for k in range(0, len(f_list)):
        ifile     = f_list[k]
        mp_person = u_list[k]
        [o_dict, m_list] = find_obsids(ifile, o_dict, m_list, mp_person)
#
#--- remove duplicate ans sort it
#
    m_list = sorted(list(set(m_list)))
#
#--- print out the scheduled list
#
    line = ''
    for obsid in m_list:
        line = line + str(obsid) + '\t' + o_dict[obsid][-1] + '\n'

    ofile = obs_ss + 'scheduled_obs_list'
    with open(ofile, 'w') as fo:
        fo.write(line)

#--------------------------------------------------------------------------------------
#-- find_file_and_mp: find all *.or files and their mp for given directory           --
#--------------------------------------------------------------------------------------

def find_file_and_mp(n_list, nchk=0):
    """
    find all *.or files and their mp for given directory
    input:  n_list  --- a list of direcotries
            nchk    --- an indicator of cartain operation (check the next month case)
    output: f_list  --- a list of directories
            u_list  --- a list of mp responsible for the directories
    """
#
#--- find all files with .or ending
#
    f_list = []
    u_list = []
    for idir in n_list:
        atemp = re.split('\s+', idir)
        tdir  = atemp[-1]
        line = ''
        chk = tdir + '/input/'
        if os.path.isdir(chk):
            if check_orfiles(chk):
                line = line + chk + '*.or '

        chk = tdir + '/scheduled/'
        if os.path.isdir(chk):
            if check_orfiles(chk):
                line = line + chk + '*.or '
    
        chk = tdir + '/pre_scheduled/'
        if os.path.isdir(chk):
            if check_orfiles(chk):
                line = line + chk + '*.or '
    
        cmd = 'ls -lrt ' + line + '> ' + zspace
        os.system(cmd)

        sd_list = mcf.read_data_file(zspace, remove=1)
        sd_list.reverse()
#
#--- use the lastest valid file
#
        for dfile in sd_list:
            mc = re.search('\.or', dfile)
            if mc is None:
                continue

            try:
                atemp = re.split('\/', dfile)
                btemp = re.split('\.', atemp[-1])
                ctemp = re.split('_',  btemp[0])
                chk   = ctemp[1][0]
            except:
                continue

            if mcf.is_neumeric(chk) or (nchk==0 and (chk in chr_list)):
                dtemp = re.split('\s+', dfile)
                f_list.append(dtemp[-1])
                u_list.append(dtemp[2])
    
    return [f_list, u_list]


#--------------------------------------------------------------------------------------
#-- check_orfiles: check whether *.or fies exist in the directory                    --
#--------------------------------------------------------------------------------------

def check_orfiles(sdir):
    """
    check whether *.or fies exist in the directory
    input:  sdir    --- a full direcotry path
    oupput: True/False
    """
    cmd = 'ls ' + sdir + '>' + zspace
    os.system(cmd)
    with open(zspace, 'r') as f:
        out = f.read()

    mc = re.search('\.or', out)
    if mc is not None:
        return True
    else:
        return False

#--------------------------------------------------------------------------------------
#-- find_obsids: find obsids and their related information                           --
#--------------------------------------------------------------------------------------

def find_obsids(ifile, o_dict, m_list, mp_person):
    """
    find obsids and their related information
    input:  ifile       --- a file name
            o_dict      --- a dictionary to keep the information about the obsids
            m_list      --- a list of obsids
            mp_person   --- mp person responsible for the data period
    output: o_dict      --- updated data dictionary
            m_list      --- updated list of obsids
    """
    data = mcf.read_data_file(ifile)

    cstep  = 0                  #--- indicator to show which area of the file
    ochk   = 0                  #--- how many times passed "OBS," marker
    ichk   = 0                  #--- how many times passed "ID" marker
    for ent in data:
#
#--- after 'SeqNbr' marker, there is a summary table
#
        if cstep == 0:
            mc1 = re.search('SeqNbr', ent)
#
#--- the summary table finishes with the following marker
#
        if cstep == 1:
            mc2 = re.search('OR QUICK LOOK END', ent)

        if cstep == 2:
            mc3 = re.search('OBS\,', ent)
            mc4 = re.search('ID',    ent)
            mc5 = re.search('CAL',   ent)
            mc6 = re.search('HETG',  ent)
            mc7 = re.search('LETG',  ent)
            mc8 = re.search('ACIS',  ent)
            mc9 = re.search('HRC',   ent)

        if cstep == 0 and mc1 is not None:
            cstep = 1
#
#--- here we are reading the summary table
#
        elif cstep == 1:
            atemp = re.split('\s+', ent)
            if mcf.is_neumeric(atemp[0]):
                try:
                    pid = int(float(atemp[1]))
                except:
                    continue
                m_list.append(pid)
#
#--- name of the target is column somewhere between 18 and 40
#
                name = ent[18:40]
                name.strip()
                o_dict[pid] = [atemp[0], name, 'None', 'CAL', mp_person]

            if mc1 is not None:
                cstep = 1
#
#--- now read more information about the obsidi
#
        elif cstep == 2:
            if mc3 is not None:
                ochk += 1
            if mc4 is not None:
                ent.strip()
#
#--- find which obsid information are presented next
#
                atemp = re.split('\,', ent)
                btemp = re.split('ID=', atemp[0]) 
                pid   = int(float(btemp[1]))

                ichk += 1
#
#--- only when ochk and ichk are equal, collect needed info
#
            if ochk == ichk:
                if mc5 is not None:
                    o_dict = update_dict(o_dict, pid, 1, 'CAL')
                if mc6 is not None:
                    o_dict = update_dict(o_dict, pid, 2, 'HETG')
                if mc7 is not None:
                    o_dict = update_dict(o_dict, pid, 2, 'LETG')
                if mc8 is not None:
                    o_dict = update_dict(o_dict, pid, 3, 'ACIS')
                if mc9 is not None:
                    o_dict = update_dict(o_dict, pid, 3, 'HRC')
        
    return [o_dict, m_list]

#--------------------------------------------------------------------------------------
#-- update_dict: update a dictionary element                                         --
#--------------------------------------------------------------------------------------

def update_dict(o_dict, pid,  pos, val):
    """
    update a dictionary element
    input:  o_dict  --- a dictionary
            pid     --- key
            pos     --- position of data update
            val     --- value to be updated
    output: o_dict  --- updated dictionary
    """
    alist       = o_dict[pid]
    alist[pos]  = val
    o_dict[pid] = alist

    return o_dict

#--------------------------------------------------------------------------------------

if __name__ == "__main__":

    find_scheduled_obs()
