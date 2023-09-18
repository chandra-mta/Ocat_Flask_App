#########################################################################################
#                                                                                       #
#       read_poc_schedule.py:   read current schedule and create a schedule data table  #
#                                                                                       #
#           author: t.isobe (tisobe@cfa.harvard.edu)                                    #
#                                                                                       #
#           last update: Sep 21, 2021                                                   #
#                                                                                       #
#########################################################################################

import os
import sys
import re
import string
import random
import time
from datetime   import datetime
import Chandra.Time
import cus_app.supple.ocat_common_functions     as ocf      #--- save commonly used functions
from flask          import current_app

#
#--- directory
#
basedir = os.path.abspath(os.path.dirname(__file__))
"""
p_file  = os.path.join(basedir, '../static/dir_list')
with  open(p_file, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec("%s = '%s'" %(var, line))
"""

#------------------------------------------------------------------------------
#-- create_schedule_data_table: read current schedule and create a schedule data table
#------------------------------------------------------------------------------

def create_schedule_data_table(ifile= ''):
    """
    read current schedule and create a schedule data table
    input:  ifile   --- input file. if it is not given
                        read from <data_dir>/schedule
    output: s_data a list of lists of data:
                    <user full name>
                    <starting time in seconds from 1998.1.1>
                    <starting time in [mm, dd, yyy]>
                    <stopping time in [mm, dd, yyy]>
                    <who assigned the slot>
                    <indicator>:    -1  ---- the row is closed for editing
                                     0  ---- the row is filled but can be re-open
                                     1  ---- the row is open 
                                     2  ---- the row is filled but a wrong time interval
                                     3  ---- the row is open with non-standard time span
                                     4  ---- same as 1, but without a delete button
                                     5  ---- same as 2, but without a delete button
                                     6  ---- same as 3, but without a delete button
                    <id of the data>
    """
#
#--- set schedule display range; start from a month ago till one year from that day
#    
    current = Chandra.Time.DateTime().secs
    t_start = current - 86400 * 30
    t_stop  = t_start + 86400 * 366
#
#--- read current schedule data
#
    if ifile == '':
        ifile   = os.path.join(current_app.config['INFO_DIR'],'schedule')

    data    = ocf.read_data_file(ifile)

    s_data  = []
    pid     = 0
    for ent in data:
        atemp = re.split('\t+', ent)
#
#--- date is in <mm>,<dd>,<yyyy>
#
        btime = convert_time_format_chandra([atemp[1], atemp[2], atemp[3]])
        etime = convert_time_format_chandra([atemp[4], atemp[5], atemp[6]])
#
#--- drop  data older than a month ago
#
        if btime < t_start:
            continue

        t_save = []
        t_save.append(atemp[0])
        t_save.append(btime)
        t_save.append([atemp[1], atemp[2], atemp[3]])
        t_save.append([atemp[4], atemp[5], atemp[6]])
        try:
            signoff = atemp[7]
        except:
            signoff = ''
        t_save.append(signoff)
#
#--- indicator to tell which rows are closed for editing (-1), which are filled (0)
#--- and which are still open(1)
#
        if btime <= current:
            t_save.append(-1)

        else:
#
#--- even if the last row is filled, some other rows before the last may be 
#--- still need to be filled; check the status by "signed off" data
#
            if atemp[0].lower == 'tbd' or signoff == '':
#
#--- check non-standard time intervals
#
                oind = check_time_interval(btime, etime)
                t_save.append(oind)

            else:
                t_save.append(0)

        t_save.append(str(pid))
        pid += 1

        s_data.append(t_save)
#
#--- fill the rest with open rows
#
    u_data = add_tbd_row(s_data[-1][3], t_stop, pid)

    if len(u_data) > 0:
        s_data = s_data + u_data

    s_data = check_neighbor(s_data)

    return s_data

#------------------------------------------------------------------------------
#-- add_tbd_row: append open data rows up to a given date to the schedule data list 
#------------------------------------------------------------------------------

def add_tbd_row(ldate, t_stop, pid):
    """
    append open data rows up to a given date to the schedule data list
    input:  ldate   --- the last closing date of the data in [<mm>,<dd>,<yyyy>]
            t_stop  --- the time to stop the open row in seconds from 1998.1.1
            pid     --- data id  (to start from)
    output: u_data  --- udated schedule data list
    """
#
#--- when convert the time into chandra time, chandra time is around 12hr
#
    s_start = convert_time_format_chandra([ldate[0], ldate[1], ldate[2]]) + 86400.0
    wday    = Chandra.Time.DateTime(s_start).wday
#
#--- weekday start from 0: Monday = 0 and Sunday = 6
#
    diff    = 6 - wday 
    s_stop  = s_start + 86400.0 * diff

    btime   = convert_time_format_chandra(s_start)
    etime   = convert_time_format_chandra(s_stop)
    
    u_data  = []
    while s_start < t_stop:
        t_save = []
        t_save.append('TBD')
        t_save.append(s_start)
        t_save.append(btime)
        t_save.append(etime)
        t_save.append('')
        t_save.append(1)
        t_save.append(str(pid))
        u_data.append(t_save)

        s_start = convert_time_format_chandra([etime[0], etime[1], etime[2]]) + 86400.0
        s_stop  = s_start + 86400 * 6

        btime   = convert_time_format_chandra(s_start)
        etime   = convert_time_format_chandra(s_stop)
        pid    += 1

    return u_data

#-------------------------------------------------------------------
#-- convert_time_format_chandra: convert date formats between chandra time and [mon, day, year]
#-------------------------------------------------------------------

def convert_time_format_chandra(itime, chk=0):
    """
    convert date formats between chandra time and [mon, day, year]
    input:  itime   --- either chandra time or a list of [mon, day, year]
            chk     --- if chk > 0, remove a leading zero
    output: etime   --- either chandra time or a list of [mon, day, year]
    """
#
#--- mon, day, year to chandra time (chandra time is at 12hr)
#
    if type(itime) == list:
        [mon, day, year] = itime
        ltime            = year  + '-' + ocf.add_leading_zero(mon, 2) 
        ltime            = ltime + '-' + ocf.add_leading_zero(day, 2)
        ltime            = time.strftime('%Y:%j:12:00:00', time.strptime(ltime, '%Y-%m-%d'))
        etime            = Chandra.Time.DateTime(ltime).secs
#
#--- chandra time to mon, day, year
#
    else:
        ltime            = Chandra.Time.DateTime(itime).date
#
#--- second part of the chandara.time.datetime output has a dicimal part; remove that part
#
        atemp            = re.split('\.', ltime)
        ltime            = atemp[0]
        ltime            = time.strftime('%m-%d-%Y', time.strptime(ltime, '%Y:%j:%H:%M:%S'))
        etime            = re.split('-', ltime)
        for k in range(0, 3):
            etime[k] = str(int(etime[k]))

    return etime

#-------------------------------------------------------------------
#-- check_time_interval: check duty span is a standard (Mon - Sun)--
#-------------------------------------------------------------------

def check_time_interval(input1, input2):
    """
    check duty span is a standard (Mon - Sun) (only for open rows)
    note: this applies only for open rows
    input:  input1  --- either starting time in chandra time
                        or schedule data table
            input2  --- either stopping time in chandra time
                        of row id
    output: if standard, return 1, else 3
    """
#
#--- if the schedule table is given, get starting and stopping time
#--- from the schedule data table
#
    if isinstance(input1, int) or isinstance(input1, float):
        stime  = input1
        etime  = input2
        add    = 0
    else:
        stime  = convert_time_format_chandra(input1[input2][2])
        etime  = convert_time_format_chandra(input1[input2][3])
        add    = update_status_ind(input1, input2)

    wstart = Chandra.Time.DateTime(stime).wday
    wstop  = Chandra.Time.DateTime(etime).wday
#
#-- checking the case the interval is more than one week
#
    diff   = etime - stime
    if diff < 0 or diff > 691200:
        chk =  1
    else:
        chk = 0

    if chk == 0 and wstart == 0 and wstop == 6:
        add += 1
        return add

    else:
        add += 3
        return add

#-------------------------------------------------------------------
#-- check_neighbor: check whether neighbot rows are already signed up and update status
#-------------------------------------------------------------------

def check_neighbor(schedule):
    """
    check whether neighbor rows are already signed up and update status
    input:  schedule    --- a schedule data table
    output: schedule    --- status updated schedule data table
                            if both neighobr is filled, add 3 to the
                            status colum to indicate no display of
                            'delete' bottun on the open rows
    """
    for k in range(1, len(schedule)-1):
        if schedule[k][-2] <= 0:
            continue
        else:
            schedule[k][-2] += update_status_ind(schedule, k)

    return schedule

#-------------------------------------------------------------------
#-- update_status_ind: check whether rows one before and one after are still open
#-------------------------------------------------------------------

def update_status_ind(schedule, cid):
    """
    check whether rows one before and one after are still open
    input:  schedule    --- schedule data table
            cid         --- row id
    output: add         --- 0: if at least one of the rwos are still oepn
                            3: if both rows are filled
    """
    bpoc = schedule[cid-1][0]
    apoc = schedule[cid+1][0]
    if bpoc != 'TBD' and apoc != 'TBD':
        add = 3
    else:
        add = 0

    return add
