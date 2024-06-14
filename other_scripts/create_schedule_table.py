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
import os
import time
import Chandra.Time
from dotenv import dotenv_values
import argparse

#
#--- Load the running application version's configuration
#--- Note that loading a different .env file (such as .localhostenv
#--- or .env) allows for test version of the web applicaiton to function
#--- more easily.
#
CONFIG = dotenv_values("/data/mta4/CUS/Data/Env/.cxcweb-env")
#
#--- For Bookkeeping, these are the default variables
#
#LIVE_DIR = "/proj/web-cxc/wsgi-scripts/cus"
#USINT_DIR = "/data/mta4/CUS/www/Usint"

#
#--- Define Directory Pathing
#
USINT_DIR = CONFIG['USINT_DIR']
LIVE_DIR = CONFIG['LIVE_DIR']
TOO_CONTACT_DIR = f"{USINT_DIR}/ocat/Info_save/too_contact_info"
HOUSE_KEEPING = f"{LIVE_DIR}/other_scripts/house_keeping"

#
#--- a few emails addresses
#
CUS       = 'cus@cfa.harvard.edu'
ADMIN     = 'bwargelin@cfa.harvard.edu'
#
#--- constant related dates
#
THREE_MON = 86400 * 30 * 3
SEVEN_DAY = 86400 * 7


#---------------------------------------------------------------------------------------
#--- create_schedule_table: update schedule html page                                 --
#---------------------------------------------------------------------------------------

def create_schedule_table():
    """
    update schedule html page
    input:  none but read from <too_contact_dir>/schedule
    output: <usint_dir>/too_contact_schedule.html
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
    with open(f"{HOUSE_KEEPING}/Schedule/schedule_main_template") as f:
        head = f.read()

    with open(f"{HOUSE_KEEPING}/Schedule/schedule_tail") as f:
        tail = f.read()

    udate = time.strftime('%m/%d/%Y', time.gmtime())
    tail  = tail.replace('#UPDATE#', udate)

    line  = head + line + tail

    ofile = f"{USINT_DIR}/too_contact_schedule.html"
    with open(ofile, 'w') as fo:
        fo.write(line)
#
#--- send notifications
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
    input:  none, but read from <too_contact_dir>/schedule
    output: a dictionary of [poc, name, period, start, stop]. key: start
            key/start/stop is in <yyyy><mm><dd>
    """

    with open(f"{TOO_CONTACT_DIR}/schedule") as f:
        data = [line.strip() for line in f.readlines()]

    d_dict = {}
    k_list = []
    for ent in data:
        atemp = ent.split()
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
        key = f"{syear}{smon:>02}{sday:>02}"
        etime = f"{syear}{emon:>02}{eday:>02}"
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
    input:  none, but read from <too_contact_dir>/this_week_person_in_charge
    output: a dictionary with [ophone, cphone, hphone, email]. key: full name
    """
    with open(f"{TOO_CONTACT_DIR}/active_usint_personnel") as f:
        data = [line.strip() for line in f.readlines()]

    poc_dict = {}
    for ent in data:
        atemp  = ent.split(":")
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
#--- send out the second notification to POC: on the day of the duty starts
#
    second_notification(k_list, d_dict, poc_dict, stime)
    
#---------------------------------------------------------------------------------------
#-- check_schedule_fill: check whether the poc schedule is running out in about 3 months 
#---------------------------------------------------------------------------------------

def check_schedule_fill(k_list, stime):
    """
    check whether the poc schedule is running out in about 3 months and if so send out email
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
    if tdiff < THREE_MON:
#
#--- check when the last time this notification was sent
#
        nfile = f"{HOUSE_KEEPING}/Schedule/add_schedule_log"
        if os.path.isfile(nfile):
            with open(nfile, 'r') as f:
                l_time = float(f.read())
        else:
            l_time = 0
#
#--- if the last notification is older than 7 days, send it again
#
        cdiff = stime - l_time
        if cdiff > SEVEN_DAY:
            ifile = f"{HOUSE_KEEPING}/Schedule/add_schedule"
            subj  = 'POC Schedule Needs To Be Filled'

            send_mail(subj, ifile, {'TO': [ADMIN], 'CC': [CUS]})
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
    check the schedule is signed up on the slot two week from current
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
            ifile = f"{HOUSE_KEEPING}/Schedule/missing_schedule"
            subj  = 'POC Schedule Needs To Be Filled'

            send_mail(subj, ifile, {'TO': [ADMIN], 'CC': [CUS]})

#---------------------------------------------------------------------------------------
#-- first_notification: send first notification to POC                                --
#---------------------------------------------------------------------------------------

def first_notification(k_list, d_dict, poc_dict, stime):
    """
    send first notification to POC
    input:  k_list      --- a list of poc schedule starting time in <yyyy><mm><dd>
            d_dict      --- a dictionary of schedule information, key: <yyyy><mm>dd>
            poc_dict    --- a dictionary of poc information, key: name
            stime       --- today's time in seconds in 1998.1.1
                  <house_keeping>/Schedule/first_notification (template)
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
                ifile = f"{HOUSE_KEEPING}/Schedule/first_notification"
                name  = d_dict[k_list[k+1]][1]
                email = poc_dict[name][-1]
                subj  = 'TOO Point of Contact Duty Notification'
                send_mail(subj, ifile, {'TO': [email], 'CC': [CUS]})

                subj  = 'TOO Point of Contact Duty Notification (sent to: ' + email + ')'
                send_mail(subj, ifile, {'TO': [ADMIN], 'CC': [CUS]})
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
                ifile = f"{HOUSE_KEEPING}/Schedule/second_notification"

                name  = d_dict[k_list[k+1]][1]
                email = poc_dict[name][-1]

                subj  = 'TOO Point of Contact Duty Notification: Second Notification'
                send_mail(subj, ifile, {'TO': [email], 'CC': [CUS]})

                subj  = 'TOO Point of Contact Duty Notification: Second Notification (sent to: ' + email + ')'
                send_mail(subj, ifile, {'TO': [ADMIN], 'CC': [CUS]})

#---------------------------------------------------------------------------------------
#-- send_mail: sending email                                                          --
#---------------------------------------------------------------------------------------

def send_mail(subject, text, address_dict):
    """
    sending email
    input:  subject      --- subject line
            test         --- text or template file of text
            address_dict --- email address dictionary
    output: email sent
    """
    message = ''
    message += f"TO:{','.join(address_dict['TO'])}\n"
    if 'CC' in address_dict.keys():
        message += f"CC:{','.join(address_dict['CC'])}\n"
    if 'BCC' in address_dict.keys():
        message += f"BCC:{','.join(address_dict['BCC'])}\n"

    message += f"Subject:{subject}\n"
    
    if os.path.isfile(text):
        with open(text) as f:
            message += f.read()
    else:
        message += f"{text}"

    cmd = f"echo '{message}' | sendmail {','.join(address_dict['TO'])}"

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
                <too_contact_dir>/this_week_person_in_charge
    output: updated: <too_contact_dir>/this_week_person_in_charge
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
    pfile = f"{TOO_CONTACT_DIR}/this_week_person_in_charge"
    with open(pfile) as f:
        data = [line.strip() for line in f.readlines()]
#
#--- mark the poc who are not on duty with '#'
#
    line  = ''
    for ent in data:
        ent   = ent.replace('#', '')
        atemp = ent.split(',')
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    args = parser.parse_args()

    if args.mode == 'test':
        pass

    elif args.mode == 'flight':
        create_schedule_table()




