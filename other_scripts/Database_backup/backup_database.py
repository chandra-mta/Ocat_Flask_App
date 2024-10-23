#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#########################################################################################
#													                                    #
#       backup_database.py: backup usint related databases                              #
#													                                    #
#       Note: this script is run by mta, not cus                                        #
#                                                                                       #
#		    author: t. isobe (tisobe@cfa.harvard.edu)	                                #
#													                                    #
#		    last update: Oct 28, 2021								                    #
#													                                    #
#########################################################################################

import sys
import os
import string
import re
import time
import random
rtail  = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(rtail)

admin = 'lina.pulgarin-duque@cfa.harvard.edu'
admin = 'tisobe@cfa.harvard.edu'

#--------------------------------------------------------------------------------------
#-- backup_database: backup usint related databases                                  --
#--------------------------------------------------------------------------------------

def backup_database():
    """
    backup usint related databases
    input:  none
    output: sending email if there is some potential problems
            updated backupdatabase  --- updates_table.list
                                        approved
    """
    file1 = '/data/mta4/CUS/www/Usint/ocat/updates_table.list'
    file2 = '/data/mta4/CUS/www/Usint/ocat/approved'
    
    size1 = os.path.getsize(file1)
    size2 = os.path.getsize(file2)
    
    with open('./last_size', 'r') as f:
        data = [line.strip() for line in f.readlines()]
    
    for ent in data:
        mc = re.search('updates', ent)
        atemp = re.split(':', ent)
        if mc is not None:
            psize1 = int(atemp[1])
        else:
            psize2 = int(atemp[1])
#
#--- check updates_table.list file
#        
    chk = 0
    if compare_size(size1, psize1):
        send_warning("updates_table.list")
    else:
        cmd = 'cp -f ' + file1 + ' /data/mta4/CUS/www/Usint/ocat/Backup/.'
        os.system(cmd)
        chk += 1
#
#--- check approved file
#        
    if compare_size(size2, psize2):
        send_warning("approved")
    else:
        cmd = 'cp -f ' + file2 + ' /data/mta4/CUS/www/Usint/ocat/Backup/.'
        os.system(cmd)
        chk += 1
#
#--- update size info file if there is not nay problem
#
    if chk == 2:
        line = 'updates:' + str(size1) + '\n'
        line = line + 'approved:' + str(size2) + '\n'

        with open('./last_size', 'w') as fo:
            fo.write(line)


#--------------------------------------------------------------------------------------
#-- compare_size: check the file size change                                         --
#--------------------------------------------------------------------------------------

def compare_size(csize, psize):
    """
    check the file size change. if the new file is more than 5% smaller than the last
    something may be wrong.
    input:  csize   --- the current file size
            psize   --- the last file size
    output: True/Fale   --- if something wrong, True. otherwise False
    """
    diff = csize - psize
    if diff < 0:
        chk = abs(diff) / psize
        if chk > 0.05:
            return True

    return False

#--------------------------------------------------------------------------------------
#-- send_warning: sending a warning email                                            --
#--------------------------------------------------------------------------------------

def send_warning(name):
    """
    sending a warning email
    input:  name    --- the name of the file
    output: email send out to admin
    """
    text = 'It seems that database /data/mta4/CUS/www/Usint/ocat/' + name
    text = text + ' may have some problems. Please check. The backup data are'
    text = text = ' in /data/mta4/CUS/www/Usint/ocat/Backup.\n'

    with open(zspace, 'w') as fo:
        fo.write(text)

    cmd = 'cat ' + zspace + '|mailx -s "Subject: Please check the database" ' + admin
    os.system(cmd)

#--------------------------------------------------------------------------------------

if __name__ == "__main__":

    backup_database()
