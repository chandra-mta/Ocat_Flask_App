#!/proj/sot/ska3/flight/bin/python

#################################################################################################
#                                                                                               #
#       signoff_request.py: send out sign off request                                           #
#                                                                                               #
#               author: t. isobe (tisobe@cfa.harvard.edu)                                       #
#                                                                                               #
#               last update: Jul 26, 2024                                                       #
#                                                                                               #
#################################################################################################

import re
import sys
import os
import sqlite3
import argparse
#
#--- Define Directory Pathing
#
OCAT_DIR = "/data/mta4/CUS/www/Usint/ocat"
OBS_SS = "/data/mta4/obs_ss"
#
#--- Pull variable used in Website Test
#
sys.path.append("/data/mta4/Script/PyUsint/lib/python3.11/site-packages")
from dotenv import dotenv_values
USINT_CONFIG = dotenv_values("/data/mta4/CUS/Data/Env/.cxcweb-env")

#
#--- set a few email addresses
#
ADMIN = 'bwargelin@cfa.harvard.edu'
CUS = 'cus@cfa.harvard.edu'
TECH = 'william.aaron@cfa.harvard.edu'
LIVE_EMAIL = True

#---------------------------------------------------------------------------------------
#-- signoff_request: send out singoff request email                                   --
#---------------------------------------------------------------------------------------

def signoff_request():
    """
    send out singoff request email
    input:  none, but read from <ocat_dir>/updates_table.list
    output: email sent
    """
#
#--- find usint users
#
    usint_dict = usint_users()
#
#--- find sign-off status
#
    [obsrev, usint, o_dict] = signoff_status()
#
#--- general case
#
    glist  = find_obs(obsrev, o_dict, 0)
    if len(glist) > 0:
        [email, subject, content] = create_email(glist, 'g')
        send_email(subject, content, {"TO": email, "CC":[CUS, ADMIN]})
#
#---  acis case
#
    alist  = find_obs(obsrev, o_dict, 1)
    if len(alist) > 0:
        [email, subject, content] = create_email(alist, 'a')
        send_email(subject, content, {"TO": email, "CC":[CUS, ADMIN]})
#
#--- acis si case
#
    aslist = find_obs(obsrev, o_dict, 2)
    if len(aslist) > 0:
        [email, subject, content] = create_email(aslist, 'sa')
        send_email(subject, content, {"TO": email, "CC":[CUS, ADMIN]})
#
#--- hrc si case
#
    hslist = find_obs(obsrev, o_dict, 3)
    if len(hslist) > 0:
        [email, subject, content] = create_email(hslist, 'sh')
        send_email(subject, content, {"TO": email, "CC":[CUS, ADMIN]})
#
#--- verification signoff
#
    ulist  = find_obs(obsrev, o_dict, 4)
    if len(ulist) > 0:
#
#--- for the verification, only one email is sent per a user;
#--- so obsrevs are gathered for each usint user
#
        [users, so_dict] = group_obs(ulist)
        for user in users:
            obs_list  = so_dict[user]
            email = usint_dict[user]
            [subject, content] = verification_email(obs_list)
            send_email(subject, content, {"TO": email, "CC":[CUS, ADMIN]})

#---------------------------------------------------------------------------------------
#-- usint_users: create usint user info dictionary                                    --
#---------------------------------------------------------------------------------------

def usint_users():
    """
    create usint user info dictionary
    input:  none, but read from USINT_CONFIG
    output: d_ict   --- a dictionary of {username: email}
    """
    con = sqlite3.connect(USINT_CONFIG['DATABASE_URL'].split("///")[1])
    cur = con.cursor()
    res = cur.execute("SELECT username, email FROM User")
    d_dict = {}
    for ent in res.fetchall():
        d_dict[ent[0]] = ent[1]
    con.close()
    return d_dict

#---------------------------------------------------------------------------------------
#-- signoff_status: create a dictionary of signoff status                             --
#---------------------------------------------------------------------------------------

def signoff_status():
    """
    create a dictionary of signoff status
    input:  none, but read from <ocat_dir>/updates_table.list
    output: obsrev  --- a list of obsrev
            usint   --- a list of useint users
            o_idct  --- a dict of [<general> <acis> <acis si> <hrc si> <verify> <inst> <user id>]: key: obsrev
    """
#
#--- create obsid <--> instrument dictionary
#
    inst_d = make_obs_inst_dict()
#
#--- read database
#
    ifile = f"{OCAT_DIR}/updates_table.list"
    with open(ifile) as f:
        data = [line.strip() for line in f.readlines()]
    o_dict = {}                 #--- a dict of [<general> <acis> <si> <verify> <inst> <usint>]
    obsrev = []                 #--- a list of obsrev
    usint  = []                 #--- a list of usint user id
    for ent in data:
        chk    = 0
        atemp  = re.split('\t+', ent)

        if len(atemp) < 8:
            continue

        btemp  = re.split('\.', atemp[0])
        key    = btemp[0].lstrip('0')           #--- removing leading zeros
        inst   = inst_d[key]
        status = [0, 0, 0, 0, inst, atemp[-1]]
#
#--- check each signoff status; if it is already verified, go to the next one
#
        if atemp[5] != 'NA':
            continue 

        for k in range(0, 5):
            pos = k + 1
            if atemp[pos] == 'NA':
                status[k] = 1
                chk += 1
#
#--- if something is not signed off, include in the lists/dict
#
        if chk > 0:
            o_dict[atemp[0]] = status
            obsrev.append(atemp[0])
            usint.append(atemp[-1])

    return [obsrev, usint, o_dict]
    
#---------------------------------------------------------------------------------------
#-- make_obs_inst_dict: make a dictionary of obsid <---> instrument                  ---
#---------------------------------------------------------------------------------------

def make_obs_inst_dict():
    """
    make a dictionary of obsid <---> instrument
    input:  none, but read from <obs_ss>/sot_ocat.out
    output: dict_i  --- a dictionary of obsid <---> instrument
    """
    ifile = f"{OBS_SS}/sot_ocat.out"
    with open(ifile) as f:
        data = [line.strip() for line in f.readlines()]
    dict_i = {}
    for ent in data:
        atemp = re.split('\^', ent)
        mc1   = re.search('ACIS', atemp[12])
        mc2   = re.search('HRC',  atemp[12])
        key   = atemp[1].strip()
        if mc1 is not None:
            dict_i[key] = 'acis'
        elif mc2 is not None:
            dict_i[key] = 'hrc'
        else:
            dict_i[key] = 'other'

    return dict_i

#---------------------------------------------------------------------------------------
#-- find_obs: find which obsrev's need signoff request email                          --
#---------------------------------------------------------------------------------------

def find_obs(obsrev, o_dict, pos):
    """
    find which obsrev's need signoff request email
    input:  obsrev      --- a list of obsrev
            o_dict      --- a dictionay of [<general> <acis> <si> <verify> <inst> <usit>]
            pos         --- position of sign off checking (e.g. <acis> for pos 1)
    output: r_list      --- a list of lists of (<bosrev>, <usint>]
    """
    r_list = []
    for obs in obsrev:
#
#--- status: [<general> <acis> <acis si> <hrc si>  <verify> <inst> <user id>]
#
        status = o_dict[obs]
#
#--- check the status of the requested postion. if 0, singed off or don't need to check
#
        if status[pos] == 0:
            continue
#
#--- check the status of others come before. if one of them is not signed off, ignore this case
#
        chk = 0
        for k in range(0, pos):
            chk += status[k]
        if chk > 0:
            continue
#
#--- r_list is a list of [<obsrev>, <usint>]
#
        r_list.append([obs, status[-1]])

    return r_list

#---------------------------------------------------------------------------------------
#-- send_email: sending email                                                         --
#---------------------------------------------------------------------------------------

def send_email(subject, text, addresses):
    """
    sending email
    input:  subject      --- subject line
            test         --- text or template file of text
            addresses --- email address dictionary
    output: email sent
    """
    if LIVE_EMAIL:
        address_dict = addresses
    else:
        address_dict = {'TO':TECH}

    message = ''
    if type(address_dict['TO']) == list:
        to_email = f"{','.join(address_dict['TO'])}"
        message += f"TO:{to_email}\n"
    else:
        to_email = f"{address_dict['TO']}"
        message += f"TO:{to_email}\n"


    if 'CC' in address_dict.keys():
        if type(address_dict['CC']) == list:
            message += f"CC:{','.join(address_dict['CC'])}\n"
        else:
            message += f"CC:{address_dict['CC']}\n"
    if 'BCC' in address_dict.keys():
        if type(address_dict['CC']) == list:
            message += f"BCC:{','.join(address_dict['BCC'])}\n"
        else:
            message += f"BCC:{address_dict['BCC']}\n"

    message += f"Subject:{subject}\n"
    
    if os.path.isfile(text):
        with open(text) as f:
            message += f.read()
    else:
        message += f"{text}"

    if not LIVE_EMAIL:
        print(f"Echoing the following message into sendmail.\n{message}")
    os.system(f"echo '{message}' | sendmail -t")

#---------------------------------------------------------------------------------------
#-- create_email: create signoff request email                                       ---
#---------------------------------------------------------------------------------------

def create_email(obs, catg):
    """
    create signoff request email 
    input:  obs     --- a list of obsrev
            catg    --- indicator of which categor email is created
    output: email   --- email addresses
            subjet  --- subject line
            tline   --- content of the email
    """
    subject = ' Updates needed for obsid.revs '
    tline   = 'This message is a daily summary of obsid.revs which\nneed a signing-off of  '
#
#--- general sign off
#
    if catg == 'g':
        subject = subject + '(General sign-off)'
        tline   = tline   + 'general (non-ACIS) changes:\n\n'
        email   = ['arcops@cfa.harvard.edu']
#
#--- acis sign off
#
    elif catg == 'a':
        subject = subject + '(ACIS sign-off)'
        tline   = tline   + 'ACIS-specific changes:\n\n'
        email   = ['arcops@cfa.harvard.edu']
#
#--- acis si sign off
#
    elif catg == 'sa':
        subject = subject + '(ACIS SI sign-off)'
        tline   = tline   + 'ACIS SI-specific changes:\n\n'
        email   = ['acisdude@cfa.harvard.edu']
#
#--- hrc si sign off
# 
    elif catg == 'sh':
        subject = subject + '(HRC SI sign-off)'
        tline   = tline   + 'HRC SI-specific changes:\n\n'
        email   = ['vkashyap@cfa.harvard.edu', 'hrcdude@cfa.harvard.edu']
#
#--- create a list of obsrev in that category
#
    for ent in obs:
        tline   = tline   + '\t' + ent[0]  + '\n'

    tline = tline + '\nThese updates may be verified at the following URL:\n\n'
    tline += f"{USINT_CONFIG['HTTP_ADDRESS']}/orupdate/\n"

    return [email, subject, tline]

#---------------------------------------------------------------------------------------
#-- verification_email: create verification request email                             --
#---------------------------------------------------------------------------------------

def verification_email(obs_list):
    """
    create verification request email
    input:  obs_list    --- a list of obsrev
    output: subject     --- subject line
            tline       --- content of the email
    """
    subject = ' Verification needed for obsid.revs'
    tline   = 'All requested edits have been made for the following obsid.rev(s):\n\n'

    for ent in obs_list:
        tline = tline + '\t' +  ent + '\n'

    tline   = tline + '\nPlease sign off these requests at this url:\n\n'
    tline   = tline + f"{USINT_CONFIG['HTTP_ADDRESS']}/orupdate/\n"
    tline   = tline + '\nThis message is generated by a cron job, so no reply is necessary.\n'
    
    return [subject, tline]

#---------------------------------------------------------------------------------------
#-- group_obs: group obsrev under usint user's names                                  --
#---------------------------------------------------------------------------------------

def group_obs(udata):
    """
    group obsrev uder usint user's name
    input:  udata   --- a list of lists of [<obsrev>, <usint>]
    output: user    --- a list of users
            u_dict  --- a dict of usint <---> a list of obsrev
    """
    users  = []
    u_dict = {}
    for ent in udata:
        if ent[1] in users:
            out = u_dict[ent[1]]
            out.append(ent[0])
            u_dict[ent[1]] = out
        else:
            u_dict[ent[1]] = [ent[0]]
            users.append(ent[1])

    return [users, u_dict]
#---------------------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-p", "--path", required = False, help = "Directory path to determine output location of plot.")
    args = parser.parse_args()
#
#--- Determine if running in test mode and change pathing if so
#
    if args.mode == 'test':
        OCAT_DIR = "/proj/web-cxc/cgi-gen/mta/Obscat/ocat"
        USINT_CONFIG = dotenv_values("/data/mta4/CUS/Data/Env/.localhostenv")
        LIVE_EMAIL = False

        signoff_request()
    
    elif args.mode == 'flight':

        signoff_request()