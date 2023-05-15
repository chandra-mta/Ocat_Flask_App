#########################################################################################
#                                                                                       #
#   ocat_common_functions: a depository of functions commonly used by Ocat Data         #
#                                                                                       #
#           author: t. isobe (tisobe@cfa.harvard.edu)                                   #
#                                                                                       #
#           last update: Sep 10, 2021                                                   #
#                                                                                       #
#########################################################################################

import os
import sys
import re
import string
import random
import time
import math
import numpy
from datetime import datetime
from io import BytesIO
import codecs
import pwd
import crypt
import getpass
import pathlib
from hmac import compare_digest as compare_hash

sys.path.append('/proj/sot/ska3/flight/lib/python3.8/site-packages')
import Chandra.Time

from flask  import current_app
#
#--- directory
#
basedir = os.path.abspath(os.path.dirname(__file__))
p_file  = os.path.join(basedir, '../static/dir_list')
with  open(p_file, 'r') as f:
    data = [line.strip() for line in f.readlines()]

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec("%s = '%s'" %(var, line))
#
#--- temporary writing space
#
tail = int(time.time() * random.random())
zspace = '/tmp/zspace' + str(tail)

#--------------------------------------------------------------------------
#-- read_data_file: read a data file and create a data list              --
#--------------------------------------------------------------------------

def read_data_file(ifile, remove=0, ctype='r'):
    """
    read a data file and create a data list
    input:  ifile   --- input file name
            remove  --- if > 0, remove the file after reading it
            ctype   --- reading type such as 'r' or 'b'
    output: data    --- a list of data
    """
#
#--- if a file specified does not exist, return an empty list
#
    if not os.path.isfile(ifile):
        return []

    try:
        with open(ifile, ctype) as f:
            data = [line.strip() for line in f.readlines()]
    except:
        with codecs.open(ifile, ctype, encoding='utf-8', errors='ignore') as f:
            data = [line.strip() for line in f.readlines()]
#
#--- if asked, remove the file after reading it
#
    if remove > 0:
        rm_files(ifile)

    return data

#--------------------------------------------------------------------------
#-- rm_files: remove a file of named file in a list                      --
#--------------------------------------------------------------------------

def rm_files(ifile):
    """
    remove a file of named file in a list
    input:  ifile   --- a file name or a list of file names to be removed
    output: none
    """
    mc = re.search('\*', ifile)
    if mc  is not None:
        cmd = 'rm -fr ' +  ifile
        os.system(cmd)

    else:
        if isinstance(ifile, (list, tuple)):
            ilist = ifile
        else:
            ilist = [ifile]
    
        for ent in ilist:
            if os.path.isfile(ent):
                cmd = 'rm -fr ' + ent
                os.system(cmd)

def rm_file(ifile):
    rm_files(ifile)

#--------------------------------------------------------------------------
#-- sort_list_with_other: order a list with the order of another sorted list 
#--------------------------------------------------------------------------

def sort_list_with_other(list1, list2, schoice=1):
    """
    order a list with the order of another sorted list
    input:  list1           --- a list
            list2           --- a list
            schoice         --- which list to be used to order; default:first
    output: list1, list2    --- sorted/reordered lists
    """
    if len(list1) != len(list2):
        return False

    if schoice == 1:
        list1, list2 = (list(t) for t in zip(*sorted(zip(list1, list2))))
    else:
        list2, list1 = (list(t) for t in zip(*sorted(zip(list2, list1))))

    return [list1, list2]

#--------------------------------------------------------------------------
#-- sort_multi_list_with_one: order all lists in a list by nth list order -
#--------------------------------------------------------------------------

def sort_multi_list_with_one(clists, col=0):
    """
    order all lists in a list by nth list sorted order
    input:  clist   --- a list of lists
            col     --- position of a list to be use for sorting
    output: save    --- a list of lists, sorted
    """

    array1 = numpy.array(clists[col])
    index  = numpy.argsort(array1)

    save   = []
    for ent in clists:
        save.append(list(numpy.array(ent)[index]))

    return save

#--------------------------------------------------------------------------
#-- is_leapyear: check whether the year is a leap year                   --
#--------------------------------------------------------------------------

def is_leapyear(year):
    """
    check whether the year is a leap year
    input:  year    --- year
    output: True/False
    """
    year = int(float(year))
    chk  = year % 4             #--- every 4 years:   leap year
    chk2 = year % 100           #--- but every 100 years: not leap year
    chk3 = year % 400           #--- except every 400 year: leap year

    val  = False
    if chk == 0:
        val = True
        if chk2 == 0:
            val = False
    if chk3 == 0:
        val = True

    return val

def isLeapYear(year):
    is_leapyear(year)
    
#--------------------------------------------------------------------------
#-- is_neumeric: checking the input is neumeric value                    --
#--------------------------------------------------------------------------

def is_neumeric(val):
    """
    checking the input is neumeric value
    input:  val --- input value
    output: True/False
    """

    try:
        var = float(val)
        return True
    except:
        return False

def chkNumeric(val):
    is_neumeric(val)

#--------------------------------------------------------------------------
#--------------------------------------------------------------------------
#--------------------------------------------------------------------------

def is_integer(val):
    """
    check the value is interger and if so return interger
    input:  val --- input value. can be string
    output: val --- interger if it is interger/float, if it is float/ string 
    """

    if is_neumeric(val):
        fval = float(val)
        val  = int(fval)
        if val == fval:
            return val
        else:
            return fval
    else:
        return val

#--------------------------------------------------------------------------
#-- add_leading_zero: add leading 0 to digit                             --
#--------------------------------------------------------------------------

def add_leading_zero(val, dlen=2):
    """
    add leading 0 to digit
    input:  val     --- neumeric value or string value of neumeric
            dlen    --- length of digit
    output: val     --- adjusted value in string
    """
    try:
        val = int(val)
    except:
        return val

    val  = str(val)
    vlen = len(val)
    for k in range(vlen, dlen):
        val = '0' + val

    return val

#--------------------------------------------------------------------------
#-- add_tailing_zero: add '0' to the end to fill the length after a dicimal point
#--------------------------------------------------------------------------

def add_tailing_zero(val, digit):
    """
    add '0' to the end to fill the length after a dicimal point
    input:  val --- value
            digit   --- the number of decimal position
    output: val --- adjust value (str)
    """
    val   = str(val)
    atemp = re.split('\.', val)
    
    vlen  = len(atemp[1])
    diff  = digit - vlen
    if diff > 0:
        for k in range(0, diff):
            atemp[1] = atemp[1] + '0'
    
    val   = atemp[0] + '.' + atemp[1]
    
    return val

#--------------------------------------------------------------------------
#-- change_month_format: cnvert month format between digit and three letter month 
#--------------------------------------------------------------------------

def change_month_format(month):
    """
    cnvert month format between digit and three letter month
    input:  month   --- either digit month or letter month
    oupupt: either digit month or letter month
    """
    m_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',\
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
#
#--- check whether the input is digit
#
    try:
        var = int(float(month))
        if (var < 1) or (var > 12):
            return 'NA'
        else:
            return m_list[var-1]
#
#--- if not, return month #
#
    except:
        mon = 'NA'
        var = month.lower()
        for k in range(0, 12):
            if var == m_list[k].lower():
                return k+1

        return mon

#--------------------------------------------------------------------------
#-- separate_data_into_col_data: separate a list of data lines into a list of lists 
#--------------------------------------------------------------------------

def separate_data_into_col_data(data, spliter = '\s+'):
    """
    separate a list of data lines into a list of lists of column data
    input:  data    --- data list
            spliter --- spliter of the line. default: \s+
    output: save    --- a list of lists of data
    """
    atemp = re.split(spliter, data[0])
    alen  = len(atemp)
    save  = [[] for x in range(0, alen)]   

    for ent in data:
        atemp = re.split(spliter, ent)
        for k in range(0, alen):
            try:
                val = float(atemp[k])
            except:
                val = atemp[k].strip()
     
            save[k].append(val)
     
    return save

#--------------------------------------------------------------------------
#-- remove_non_neumeric_values: remove all rows of lists in a list which correspond to non-neumeric
#--------------------------------------------------------------------------

def remove_non_neumeric_values(alist, pos):
    """
    remove all rows of lists in a list which correspond to non-neumeric
    entries in pos-th list.
    input:  alist   --- a list of lists
            pos     --- position of a list which contains non nuemeric values
    output: slist   --- a list of lists removed non-neumeric entries
    """
#
#--- get a list of which we want to find non-numeric entries
#
    tlist  = alist[pos]
    tlist  = genfromtxt3(tlist)
    tarray = numpy.array(tlist)
#
#--- create index to remove non-neumeric values
#
    oindex = ~numpy.isnan(tarray)
#
#--- apply the index to all lists
#
    slist  = []
    for ent in alist:
        tarray = numpy.array(ent)
#
#--- make sure that all entries are numeric not string
#
        nlist  = list(tarray[oindex])
        if isinstance(nlist[0], str):
            nlist = list(genfromtxt3(nlist))

        slist.append(nlist)

    return slist

#------------------------------------------------------------------------------
#-- read_user: read user <---> hashed password list and create a dict        --
#------------------------------------------------------------------------------

def read_user():
    """
    read user <---> hashed password list and create a dict
    input:  none
    output: udict   ---- a dict of user <---> hashed password
    """
    pfile = '/data/mta4/CUS/www/Usint/Pass_dir/.htpasswd'
    data  = read_data_file(pfile)
    udict = {}
    for ent in data:
        atemp = re.split(':', ent)
        udict[atemp[0]] = atemp[1].strip()

    return udict

#------------------------------------------------------------------------------
#-- check_password: compare password against hashed password value           --
#------------------------------------------------------------------------------

def check_password(cleartext, cryptedpasswd):
    """
    compare password against hashed password value
    input:  cleartext       --- typed password
            cryptedpasswd   --- hashed password
    output: True/False
    """

    if cryptedpasswd:
        if cryptedpasswd == 'x' or cryptedpasswd == '*':
            raise ValueError('no support for shadow passwords')

        return compare_hash(crypt.crypt(cleartext, cryptedpasswd), cryptedpasswd)
    else:
        return  False

#--------------------------------------------------------------------------
#-- find_other_revisions: find other revisions of the same obsid         --
#--------------------------------------------------------------------------

def find_other_revisions(obsid, rev=0):
    """
    find other revisions of the same obsid
    input:  obsid       --- obsid
            rev         --- rev # of the current data
                            if 0, find all revisions
    output: other_rev   --- a list of html link to the other rev
    """
    #cmd  = 'ls ' + ocat_dir + 'updates/' + obsid + '.* > ' + zspace
    #os.system(cmd)

    #data = read_data_file(zspace, remove=1)

    data = [each for each in os.listdir(f"{ocat_dir}/updates/") if each.startswith(str(obsid)+".")]
    rev       = int(rev)
    other_rev = []
    for ent in data:
        atemp = re.split('\/', ent)
        btemp = re.split('\.', atemp[-1])
        crev  = int(btemp[-1])
        if crev != rev:
            if atemp[-1] != '':
                other_rev.append(atemp[-1])

    other_rev = sorted(other_rev)

    return other_rev

#-------------------------------------------------------------------
#-- read_poc_list: read current poc from the list                 --
#-------------------------------------------------------------------

def read_poc_list(cuser=''):
    """ 
    read current poc from the list 
    input:  <data_dir>/active_usint_personal
            cuser   --- current user. if it is given the information
                        will be float up to the top of the list
    output: a list of [<poc id>, <Full Name>, <email address>]
    """
    ifile = info_dir + 'active_usint_personal'
    data  = read_data_file(ifile)

    poc_list = []
    save     = []
    for ent in data:
        if ent[0] == '#':
            continue

        atemp = re.split(':', ent)
        t_list = [atemp[0], atemp[1], atemp[-1]]
#
#--- keep the current user info to the side
#
        if cuser != '':
            if cuser == atemp[0]:
                save = t_list
            else:
                poc_list.append(t_list)
        else:
            poc_list.append(t_list)
#
#--- sort the list and if the currnent user is given, add to the top
#
    poc_list = sorted(poc_list, key=lambda x: x[1])
    if cuser != '' and len(save) > 0:
        poc_list = [save] + poc_list

    return poc_list

#-------------------------------------------------------------------
#-- set_year_list: create a year list for a pulldown menu         --
#-------------------------------------------------------------------

def set_year_list(chk=0):
    """
    create a year list for a pulldown menu
    input:  chk         --- if == 0, return a list of integer year, 
                            otherwise string year
    output: year_list   --- a list of years starting from the last year
    """
    tyear = int(time.strftime('%Y', time.gmtime()))
    year_list = []
    for year in range(tyear -1, tyear+5):

        if chk == 0:
            year_list.append(year)
        else:
            year_list.append(str(year))

    return year_list

#-------------------------------------------------------------------
#-------------------------------------------------------------------
#-------------------------------------------------------------------

def convert_chandra_time_to_display(ctime):

    ltime = Chandra.Time.DateTime(ctime).date
    atemp = re.split('\.', ltime)
    ltime = atemp[0]

    ltime = time.strftime('%Y-%m-%d-%H:%M:%S', time.strptime(ltime, '%Y:%j:%H:%M:%S'))
    atemp = re.split('-', ltime)

    return atemp
    
#-------------------------------------------------------------------
#-------------------------------------------------------------------
#-------------------------------------------------------------------

def convert_chandra_time_to_display2(ctime, tformat='%Y-%m-%d-%H:%M:%S'):

    ltime = Chandra.Time.DateTime(ctime).date
    atemp = re.split('\.', ltime)
    ltime = atemp[0]

    ltime = time.strftime(tformat, time.strptime(ltime, '%Y:%j:%H:%M:%S'))

    return ltime
    
#-------------------------------------------------------------------
#-- is_file_locked: check whether the file is locked              --
#-------------------------------------------------------------------

def is_file_locked(filepath):
    """
    check whether the file is locked
    input:  filepath    --- a full path to the file
    output: True/False
    """
    locked      = False
    file_object = None
    if os.path.exists(filepath):
        try:
#
#--- opening file in append mode and read the first 8 char
#
            buffer_size = 8
            file_object = open(filepath, 'a', buffer_size)
            if file_object:
                locked = False
        except:
            locked = True

        finally:
            if file_object:
                file_object.close()

    return locked

#-------------------------------------------------------------------
#-- sleep_while_locked: sleep until the file is unlocked          --
#-------------------------------------------------------------------

def sleep_while_locked(ifile, tmax=10):
    """
    sleep until the file is unlocked
    input:  ifile   --- a file with a full path
            tmax    --- max time to sellp: defalut 10 secs
                        if the max time is passed, False is returned
    output: True/False  
    """
    step = 0.1
    dlen = int(tmax / step)

    chk  = False
    for k in range(0, dlen):
        if is_file_locked(ifile):
            sleep(step)
        else:
            chk = True
            break

    return chk 

#-------------------------------------------------------------------
#-- clean_tmp_files: remove temp files kept in /tmp/ directory    --
#-------------------------------------------------------------------
#If no futher errors for the removal of zspace directorys, then this cleanupfunction can safely be removed.
def clean_tmp_files():
    """
    remove temp files kept in /tmp/ directory  (a day old)
    input:  none but check /tmp/zspace*
    output: cleaned /tmp/ dir
    """
    now = Chandra.Time.DateTime().secs
    cmd = 'touch ' + zspace
    os.system(cmd)
    cmd = 'ls /tmp/zspace* > ' + zspace 
    os.system(cmd)

    data = read_data_file(zspace, remove=1)
    for ent in data:
        if os.path.isfile(ent):
            stime = find_file_creation_time(ent)
            diff  = now - stime
            if diff > 86000:
                try:
                    rm_files(ent)
                except:
                    pass

#-----------------------------------------------------------------------------------------------
#-- find_file_creation_time: find out a file creation time in Chandra Time                    --
#-----------------------------------------------------------------------------------------------

def find_file_creation_time(ifile):
    """
    find out a file creation time in Chandra Time
    input:  ifile   --- a file name with a full file path
    output: stime   --- a file creating time in sec from 1998.1.1
    """
    if os.path.isfile(ifile):
        fname = pathlib.Path(ifile)
        mtime = datetime.fromtimestamp(fname.stat().st_ctime)
        atemp = re.split('\s+', str(mtime))
        ltime = time.strftime('%Y:%j:00:00:00', time.strptime(atemp[0], '%Y-%m-%d'))
        stime = int(Chandra.Time.DateTime(ltime).secs)
    else:
        stime = None

    return stime

#-----------------------------------------------------------------------------------------------
#-- find_file_modification_time: find out a file modification time in Chandra Time            --
#-----------------------------------------------------------------------------------------------

def find_file_modification_time(ifile):
    """
    find out a file modification time in Chandra Time
    input:  ifile   --- a file name with a full file path
    output: stime   --- a file modification time in sec from 1998.1.1
                        if the file does not exist, return -10000
    """
    if os.path.isfile(ifile):
#
#--- 883612800 = calendar.timegm(time.strptime('1998:001:00:00:00', '%Y:%j:%H:%M:%S'))
#
        stime = int(float(os.path.getmtime(ifile) - 883612800))
    else:
        stime = -10000

    return stime

#-----------------------------------------------------------------------------------------------
#-- convert_ra_dec_format: convert ra/dec fromat between <dd>:<mm>:<ss> or <dd.ddddd> format  --
#-----------------------------------------------------------------------------------------------

def convert_ra_dec_format(dra, ddec):
    """
    convert ra/dec format
    input:  dra     --- either <hh>:<mm>:<ss> or <dd.ddddd> format
            ddec    --- either <dd>:<mm>:<ss> or <ddd.ddddd> format

    output: tra     --- either <hh>:<mm>:<ss> or <dd.ddddd> format
            tdec    --- either <dd>:<mm>:<ss> or <ddd.ddddd> format
    """
#
#--- conveting a deciaml format to hh:mm:ss / dd:mm:ss format
#    
    if is_neumeric(dra):
        ra   = float(dra)
        hh   = int(ra / 15.0)
        df   = 60.0 * (ra/15.0 - hh)
        mm   = int(df)
        ss   = 60.0 * (df - mm)
        si   =int(ss)
        frac = ss - si
        frac = '%1.4f' % frac
        temp = re.split('\.', frac)
        frac = temp[1]

        tra  = '%02d:%02d:%02d.%s' % (hh, mm, si, frac)


        dec  = float(ddec)
        if dec < 0:
            sign = '-'
        else:
            sign = '+'
        dec  = abs(dec)

        dd   = int(dec)
        df   = 60.0 * (dec - dd)
        mm   = int(df)
        ss   = 60.0 * (df  - mm)
        #if ss > 60.0:
        #    ss -= 60.0
        #    mm += 1
        #if mm > 60:
        #    mm -= 60
        #    dd += 1
        si   =int(ss)
        frac = ss - si
        frac = '%1.4f' % frac
        temp = re.split('\.', frac)
        frac = temp[1]

        tdec = '%s%02d:%02d:%02d.%s' %(sign, dd, mm, si, frac)

    else:
#
#--- converting hh:mm:ss /dd:mm:ss format to a decimal format
#
#--- check mis-typing 
#
        dra  = dra.replace(';', ':')
        ddec = ddec.replace(';', ':')
#
#--- check the coordinates are separated by ":" or " " (blank space)
#
        mc = re.search(':', dra)
        if mc is not None:
            dra  = re.split(':', dra)
            ddec = re.split(':', ddec)

        else:
            dra  = re.split('\s+', dra)
            ddec = re.split('\s+', ddec)

        tra = 15.0 * (float(dra[0]) + float(dra[1]) / 60.0 + float(dra[2]) / 3600.0)
        tra = '%3.8f' % tra

        if float(ddec[0]) < 0:
            sign = -1
        else:
            sign =  1

        tdec = sign * (abs(float(ddec[0])) + float(ddec[1]) / 60.0 + float(ddec[2]) / 3600.0)
        tdec = '%3.8f' % tdec


    return tra, tdec




