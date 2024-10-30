#!/proj/sot/ska3/flight/bin/python

#
#--- backup_database.py: backup usint related databases
#--- author: w. aaron (william.aaron@cfa.harvard.edu)
#--- last update: Oct 25, 2024
#

import sys
sys.path.append("/data/mta4/Script/Python3.11/lib/python3.11/site-packages")
import os
from dotenv import dotenv_values
import argparse
import getpass

TECH = 'william.aaron@cfa.harvard.edu'
CC = 'mtadude@cfa.harvard.edu'
CONFIG = dotenv_values("/data/mta4/CUS/Data/Env/.cxcweb-env")
USINT_DIR = CONFIG['USINT_DIR']
OCAT_DIR = f"{USINT_DIR}/ocat"
BACKUP_DIR = f"{OCAT_DIR}/Backup"

#--------------------------------------------------------------------------------------
#-- backup_database: backup usint related databases                                  --
#--------------------------------------------------------------------------------------

def backup_database():
    """
    Backup Usint related databases
    input:  None
    output: Create a backup of updates_table.db and approved files
            Also send a warning email if there is some potential problems with database integrity
    """
    if compare_size(f"{OCAT_DIR}/updates_table.db", f"{BACKUP_DIR}/updates_table.db"):
        os.system(f"cp -f --preserver--all {OCAT_DIR}/updates_table.db {BACKUP_DIR}/updates_table.db")
    else:
        text = f"{OCAT_DIR}/updates_table.db file is over 5% smaller than back up in {BACKUP_DIR}.\n"
        text += "Please check the backup and live databases.\n"
        text += f"This message was sent to {TECH} and {CC}."
        send_mail("Check Usint Backup: updates_table.db", text, {"TO":TECH, "CC": CC})
    
    if compare_size(f"{OCAT_DIR}/approved", f"{BACKUP_DIR}/approved"):
        os.system(f"cp -f --preserver--all {OCAT_DIR}/approved {BACKUP_DIR}/approved")
    else:
        text = f"{OCAT_DIR}/approved file is over 5% smaller than back up in {BACKUP_DIR}.\n"
        text += "Please check the backup and live databases.\n"
        text += f"This message was sent to {TECH} and {CC}."
        send_mail("Check Usint Backup: approved", text, {"TO":TECH, "CC": CC})


#--------------------------------------------------------------------------------------
#-- compare_size: check the file size change                                         --
#--------------------------------------------------------------------------------------

def compare_size(old, new):
    """
    check the file size change. if the new file is more than 5% smaller than the last
    something may be wrong.
    input:  old --- old file
            new --- new file
    output: True/False   --- if something wrong, return False. If size comparison is fine, return True
    """
    diff = os.path.getsize(new) - os.path.getsize(old)
    if diff < 0:
        chk = abs(diff) / os.path.getsize(old)
        if chk > 0.05:
            return True

    return False

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

    os.system(f"echo '{message}' | sendmail -t")

#--------------------------------------------------------------------------------------

if __name__ == "__main__":

    backup_database()
