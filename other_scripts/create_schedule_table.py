#!/proj/sot/ska3/flight/bin/python

#################################################################################################
#                                                                                               #
#   create_schedule_table.py: create a html page from a given schedule                          #
#                                                                                               #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                               #
#               last update: Jun 07, 2021                                                       #
#                                                                                               #
#################################################################################################

import math
import re
import sys
import os
import string
import time
import Chandra.Time
import numpy
#
#--- reading directory list
#
path = '/data/mta4/CUS/www/Usint/Ocat/ocat/other_scripts/house_keeping/dir_list'
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
odir = ocat_dir + 'app/supple/'
sys.path.append(odir)
#
#--- cus common functions
#
import ocat_common_functions         as ocf
#
#--- temp writing file name
#
#import random
#rtail     = int(time.time() * random.random())
#zspace    = '/tmp/zspace' + str(rtail)
#
#--- a few emails addresses
#
cus       = 'cus@cfa.harvard.edu'
admin     = 'bwargelin@cfa.harvard.edu'
tech      = 'tisobe@cfa.harvard.edu'
#
#--- constant related dates
#
three_mon = 86400 * 30 * 3
seven_day = 86400 * 7

#---------------------------------------------------------------------------------------
#--- create_schedule_table: update schedule html page                                 --
#---------------------------------------------------------------------------------------

def create_schedule_table():
    """
    update schedule html page
    input:  none but read from <data_dir>/too_contact_info/schedule
    output: <ocat_dir>/too_contact_schedule.html
    """
#
#--- find today's date
#
    ltime = time.strftime('%Y:%j:%H:%M:%S', time.gmtime())
    stime = int(Chandra.Time.DateTime(ltime).secs)
#
#--- read poc info
#
    poc_dict = read_poc_info()
#
#--- read schedule table
#
    [k_list, d_dict] = read_schedule()
    k_list = sorted(k_list)
    for m in range(0, len(k_list)):
        ctime = dtime_to_ctime(k_list[m])
        if ctime > stime:
            sind = m - 5
            if sind < 0:
                sind = 0
            break

    line = ''
    for key in k_list[sind:]:
        [poc, name, period, start, stop] = d_dict[key]
        if name == 'TBD':
            ophone = ' --- ' 
            cphone = ' --- ' 
            hphone = ' --- ' 
            email  = ' --- '    
        else:
            [ophone, cphone, hphone, email]  = poc_dict[name]

        start = dtime_to_ctime(start)
        stop  = dtime_to_ctime(stop)

        if (stime >= start) and (stime < stop):
            line = line + '<tr style="color:blue; background-color:lime">'
        else:
            line = line + '<tr>'
        line = line + '<td style="text-align:center;">' + period + '</td>'
        line = line + '<td style="text-align:center;">' + name   + '</td>'
        line = line + '<td style="text-align:center;">' + ophone + '</td>'
        line = line + '<td style="text-align:center;">' + cphone + '</td>'
        line = line + '<td style="text-align:left;">'   + hphone + '</td>'
        line = line + '<td style="text-align:left;">'   
        line = line + '<a href="mailto:' + email + '">'
        line = line + email  + '</a></td>'
        line = line + '</tr>\n'

#
#--- read templates
#
    ifile = house_keeping + 'Schedule/schedule_main_template'
    head  = read_template(ifile)

    ifile = house_keeping + 'Schedule/schedule_tail'
    tail  = read_template(ifile)

    udate = time.strftime('%m/%d/%Y', time.gmtime())
    tail  = tail.replace('#UPDATE#', udate)

    line  = head + line + tail

    ofile = ocat_dir + 'too_contact_schedule.html'
    with open(ofile, 'w') as fo:
        fo.write(line)
#
#--- send notificaitons
#
    schedule_notification(k_list, d_dict, poc_dict, stime)
#
#--- update this week's poc list
#
    update_this_week_poc(k_list, d_dict, poc_dict, stime)

#---------------------------------------------------------------------------------------
#-- read_schedule: read the schedule data table                                       --
#---------------------------------------------------------------------------------------

def read_schedule():
    """
    read the schedule data table
    input:  none, but read from <data_dir>/too_contact_info/schedule
    output: a dictionary of [poc, name, period, start, stop]. key: start
            key/start/stop is in <yyyy><mm><dd>
    """

    ifile = data_dir + 'too_contact_info/schedule'
    data  = ocf.read_data_file(ifile)

    d_dict = {}
    k_list = []
    for ent in data:
        atemp = re.split('\t+',  ent)
        name  = atemp[0]
        smon  = atemp[1]
        sday  = atemp[2]
        syear = atemp[3]
        emon  = atemp[4]
        eday  = atemp[5]
        eyear = atemp[6]
        try:
            poc   = atemp[7]
        except:
            poc = 'TBD'
        key   = syear + ocf.add_leading_zero(smon) + ocf.add_leading_zero(sday)
        etime = eyear + ocf.add_leading_zero(emon) + ocf.add_leading_zero(eday)
        lsmon = change_to_letter_month(smon)
        start = lsmon + ' ' + sday
        lemon = change_to_letter_month(emon)
        stop  = lemon + ' '   + eday
        period= start + ' - ' + stop

        k_list.append(key)
        d_dict[key] = [poc, name, period, key, etime]

    return[k_list, d_dict]

#---------------------------------------------------------------------------------------
#-- change_to_letter_month: convert month format between digit and letter month       --
#---------------------------------------------------------------------------------------

def change_to_letter_month(month):
    """
    convert month format between digit and letter month
    input:  month   --- digit month 
    oupupt: either digit month or letter month
    """
    m_list = ['January', 'February', 'March', 'April', 'May', 'June', 'July',\
              'August', 'September', 'October', 'November', 'December']

    var = int(float(month))
    if (var < 1) or (var > 12):
        return 'NA'
    else:
        return m_list[var-1]

#---------------------------------------------------------------------------------------
#-- read_poc_info: read poc information                                               --
#---------------------------------------------------------------------------------------

def read_poc_info():
    """
    read poc information
    input:  none, but read from <data_dir>/too_contact_info/this_week_person_in_charge
    output: a dictionary with [ophone, cphone, hphone, email]. key: full name
    """
    ifile    = data_dir + 'too_contact_info/active_usint_personal'
    data     = ocf.read_data_file(ifile)
    poc_dict = {}
    for ent in data:
        atemp  = re.split(':', ent)
        key    = atemp[1]
        ophone = atemp[2]
        cphone = atemp[3]
        hphone = atemp[4]
        email  = atemp[5]
        poc_dict[key] = [ophone, cphone, hphone, email]

    return poc_dict

#---------------------------------------------------------------------------------------
#-- schedule_notification: sending out various notifications                          --
#---------------------------------------------------------------------------------------

def schedule_notification(k_list, d_dict, poc_dict, stime):
    """
    sending out various notifications
    input:  k_list      --- a list of poc schedule starting time in <yyyy><mm><dd>
            d_dict      --- a dictionary of schedule information, key: <yyyy><mm>dd>
            poc_dict    --- a dictionary of poc informaiton, key: name
            stime       --- today's time in seconds in 1998.1.1
    output: email sent
    """
#
#--- check whether poc schedule is filled beyond 3 months from today
#
    check_schedule_fill(k_list, stime)
#
#--- check whether the schedule two weeks from now is signed up
#
    check_next_week_filled(k_list, d_dict, stime)
#
#--- send out the first notification to POC: a day before the duty starts
#
    first_notification(k_list, d_dict, poc_dict, stime)
#
#--- send out the second notificaiton to POC: on the day of the duty starts
#
    second_notification(k_list, d_dict, poc_dict, stime)
    
#---------------------------------------------------------------------------------------
#-- check_schedule_fill: check whether the poc schedule is running out in about 3 months 
#---------------------------------------------------------------------------------------

def check_schedule_fill(k_list, stime):
    """
    check whether the poc schedule is running out in about 3 months and ifi so send out email
    input:  k_list  --- a list of poc schedule starting time in <yyyy><mm><dd>
            stime   --- today's time in seconds in 1998.1.1
            it also read: <house_keeping>/Schedule/add_scehdule_log (the last logged time)
                          <house_keeping>/Schedule/add_schedule (template)
    output: email sent
    """
#
#--- find the last entry date of the signed-up list
#
    l_entry = dtime_to_ctime(k_list[-1])
#
#--- check whether the last entry date is less than three months away
#
    tdiff   = l_entry - stime
    if tdiff < three_mon:
#
#--- check when the last time this notification was sent
#
        nfile = house_keeping + 'Schedule/add_schedule_log'
        if os.path.isfile(nfile):
            with open(nfile, 'r') as f:
                l_time = float(f.read())
        else:
            l_time = 0
#
#--- if the last notification is older than 7 days, send it again
#
        cdiff = stime - l_time
        if cdiff > seven_day:
            ifile = house_keeping +'Schedule/add_schedule'
            subj  = 'POC Schedule Needs To Be Filled'

            send_mail(subj, ifile, admin)
#
#--- update log time
#
        with open(nfile, 'w') as fo:
            fo.write(str(stime))

#---------------------------------------------------------------------------------------
#-- check_next_week_filled: check the schedule is signed up on the slot two week from currnet
#---------------------------------------------------------------------------------------

def check_next_week_filled(k_list, d_dict, stime):
    """
    check the schedule is signed up on the slot two week from currnet
    input:  k_list  --- a list of poc schedule starting time in <yyyy><mm><dd>
            d_dict  --- a dictionary of schedule information, key: <yyyy><mm>dd>
            stime   --- today's time in seconds in 1998.1.1
                          <house_keeping>/Schedule/missing_schedule (template)
    output: email sent
    """
#
#--- find the schedule date two weeks (or two down) from the current one
#
    for k in range(0, len(k_list)):
        c_time = dtime_to_ctime(k_list[k])
        if c_time >= stime:
            pos = k + 1
            break
#
#--- find whether the slot is actually signed up
#
    poc = d_dict[k_list[pos]][1]
#
#--- if it is not signed up, send out email on this Friday to notify admin
#
    if poc == 'TBD':
        wday = int(float(time.strftime('%w', time.gmtime())))
        if wday == 5:
            ifile = house_keeping + 'Schedule/missing_schedule'
            subj  = 'POC Schedule Needs To Be Filled'

            send_mail(subj, ifile, admin)

#---------------------------------------------------------------------------------------
#-- first_notification: send first notification to POC                                --
#---------------------------------------------------------------------------------------

def first_notification(k_list, d_dict, poc_dict, stime):
    """
    send first notification to POC
    input:  k_list      --- a list of poc schedule starting time in <yyyy><mm><dd>
            d_dict      --- a dictionary of schedule information, key: <yyyy><mm>dd>
            poc_dict    --- a dictionary of poc informaiton, key: name
            stime       --- today's time in seconds in 1998.1.1
                  <house_keeping>/Schedule/first_notsfication (template)
    output: email sent
    """
#
#--- check whether the scheduled poc changes in two days
#
    ncheck = stime + 86400.0
    nstart = stime + 86400.0 * 2
#
#--- find the current period
#
    for k in range(0, len(k_list)-1):
        p1 = dtime_to_ctime(k_list[k])
        p2 = dtime_to_ctime(k_list[k+1])
        if (stime >= p1) and (stime <= p2):
#
#--- if the schedule changes in two days, send a notification
#
            if (ncheck <= p2) and (nstart >= p2):
                ifile = house_keeping + 'Schedule/first_notificatioin'
                name  = d_dict[k_list[k+1]][1]
                email = poc_dict[name][-1]
                subj  = 'TOO Point of Contact Duty Notification'
                send_mail(subj, ifile, email)

                subj  = 'TOO Point of Contact Duty Notification (sent to: ' + email + ')'
                send_mail(subj, ifile, admin)
            break
            
#---------------------------------------------------------------------------------------
#-- second_notification: send second notification to POC                              --
#---------------------------------------------------------------------------------------

def second_notification(k_list, d_dict, poc_dict, stime):
    """
    send second notification to POC
    input:  k_list      --- a list of poc schedule starting time in <yyyy><mm><dd>
            d_dict      --- a dictionary of schedule information, key: <yyyy><mm>dd>
            poc_dict    --- a dictionary of poc informaiton, key: name
            stime       --- today's time in seconds in 1998.1.1
                  <house_keeping>/Schedule/second_notification (template)
    output: email sent
    """
#
#--- check yesterday's time
#
    d_before =  stime - 86400.0
#
#--- check which period yesterday blongs
#
    for k in range(0, len(k_list)-1):
        p1 = dtime_to_ctime(k_list[k])
        p2 = dtime_to_ctime(k_list[k+1])
        if (d_before>= p1) and (d_before <= p2):
#
#--- if the schedule just changes today, send a notification
#
            if stime >= p2:
                ifile = house_keeping + 'Schedule/second_notification'

                name  = d_dict[k_list[k+1]][1]
                email = poc_dict[name][-1]

                subj  = 'TOO Point of Contact Duty Notification: Second Notification'
                send_mail(subj, ifile, email)

                subj  = 'TOO Point of Contact Duty Notification: Second Notification (sent to: ' + email + ')'
                send_mail(subj, ifile, admin)

#---------------------------------------------------------------------------------------
#-- send_mail: sending email                                                          --
#---------------------------------------------------------------------------------------

def send_mail(subject, ifile, address, cc= ''):
    """
    sending email
    input:  subject --- subject line
            ifile   --- template
            address --- email address
            cc      --- cc address if needed
    output: email sent
    """
    if cc == '':
        cmd = 'cat ' + ifile + '|mailx -s "Subject: ' + subject + ' " '
        cmd = cmd    + ' -b ' + tech  + ' -c ' + cus + ' '   + address 
    else:
        cmd = 'cat ' + ifile + '|mailx -s "Subject: ' + subject + ' " ' 
        cmd = cmd +  ' -b ' + tech +  ' -c ' + cc + ' ' + address + ' ' + cus

    os.system(cmd)

#---------------------------------------------------------------------------------------
#-- update_this_week_poc: update this_week_person_in_charge table                      -
#---------------------------------------------------------------------------------------

def update_this_week_poc(k_list, d_dict, poc_dict, stime):
    """
    update this_week_person_in_charge table
    input:  k_list      --- a list of poc schedule starting time in <yyyy><mm><dd>
            d_dict      --- a dictionary of schedule information, key: <yyyy><mm>dd>
            poc_dict    --- a dictionary of poc informaiton, key: name
            stime       --- today's time in seconds in 1998.1.1
                <data_dir>/too_contact_info/this_week_person_in_charge
    output: updated: <data_dir>/too_contact_info/this_week_person_in_charge
    """
#
#--- find the current period
#
    for k in range(0, len(k_list)-1):
        p1 = dtime_to_ctime(k_list[k])
        p2 = dtime_to_ctime(k_list[k+1])
        if (stime >= p1) and (stime < p2):
#
#--- find poc
#
            name  = d_dict[k_list[k]][1]
            break
#
#--- read the file
#
    pfile = too_dir + 'this_week_person_in_charge'
    data  = ocf.read_data_file(pfile)
#
#--- mark the poc who are not on duty with '#'
#
    line  = ''
    for ent in data:
        ent   = ent.replace('#', '')
        atemp = re.split('\,', ent)
        poc   = atemp[0]
        if poc == name:
            line = line + ent + '\n'
        else:
            line = line  + '#' + ent + '\n'
#
#--- print out the update
#
    with open(pfile, 'w') as fo:
        fo.write(line)

#---------------------------------------------------------------------------------------
#-- dtime_to_ctime: convert display time to chandra time                              --
#---------------------------------------------------------------------------------------

def dtime_to_ctime(dtime):
    """
    convert display time to chandra time
    input:  dtime   --- display time in <yyyy><mm><dd>
    output: stime   --- time in seconds from 1998.1.1
    """
    ltime = time.strftime('%Y:%j:%H:%M:%S', time.strptime(dtime, '%Y%m%d'))
    stime = int(Chandra.Time.DateTime(ltime).secs)
    
    return stime

#---------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------

def read_template(ifile):

    with open(ifile, 'r') as f:
        line = f.read()

    return line

#---------------------------------------------------------------------------------------

if __name__ == "__main__":
    
    create_schedule_table()




