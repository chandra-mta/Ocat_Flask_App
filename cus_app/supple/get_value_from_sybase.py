#!/proj/sot/ska3/flight/bin/python

#####################################################################################
#                                                                                   #
#   get_value_from_sybase.py: run sybase command for python3.8                      #
#                                                                                   #
#           author: t. isobe (tisobe@cfa.harvard.edu)                               #
#                                                                                   #
#           last update: Jan 15, 2025                                               #
#                                                                                   #
#   Note: this function must be run after setting:                                  #
#           source /soft/SYBASE16.0/SYBASE.csh                                      #
#           setenv PYTHONPATH /soft/SYBASE16.0/OCS-16_0/python/python34_64r/lib     #
#         to set sybpydb module correctely.                                         #
#         see also: set_sybase_env_and_run.py                                       #
#                                                                                   #
#####################################################################################

import sys
import os
import string
import re
import json
import time
import datetime
import ska_dbi.sqsh as sqsh
from astropy.utils.misc import JsonCustomEncoder
#
#--- set sqsh parameters
#
_SERV = 'ocatsqlsrv'
_USR = 'mtaops_internal_web'
_AUTHDIR = "/data/mta4/CUS/authorization"

def sybase_cmd(cmd, db='axafocat'):
    """Run a general sybase command

    :param cmd: sybase command
    :type cmd: str
    :param db: database in server, defaults to 'axafocat'
    :type db: str, optional
    :return: An astropy table row matching parameters.
    :rtype: astropy.table.Table
    """
#
# --- connect to sybase with Sqsh class
#
    conn = sqsh.Sqsh(dbi='sybase', server=_SERV, database = db, user = _USR, authdir = _AUTHDIR)
    result = conn.fetchall(cmd)
    return result

#------------------------------------------------------------------------------------
#-- get_value_from_sybase: run sybase command for python3.8                        --
#------------------------------------------------------------------------------------

def get_value_from_sybase(parameter_list, table, where_conditions, distinct = False, db='axafocat'):
    """Run Sybase fetch with Sqsh class

    :param parameter_list: list of observation parameters
    :type parameter_list: list(str)
    :param table: Database table
    :type table: str
    :param where_conditions: Where clause parameters
    :type where_conditions: dict(str: str, int)
    :param distinct: Boolean to include the distinct term after the select statement
    :type distinct: bool
    :param db: Database to fetch in server, defaults to 'axafocat'
    :type db: str, optional
    :return: An astropy table row matching parameters to observation results.
    :rtype: astropy.table.Table
    """
    
#
# --- connect to sybase with Sqsh class
#
    conn = sqsh.Sqsh(dbi='sybase', server=_SERV, database = db, user = _USR, authdir = _AUTHDIR)
#
# --- Construct fetching command.
#
    if distinct:
        cmd = "select distinct "
    else:
        cmd = "select "
    cmd += f"{','.join(parameter_list)} from {table}"
    clauses = []
    for key, value in where_conditions.items():
        if type(value) == str:  # noqa: E721
            clauses.append(f"{key}='{value}'")
        else:
            clauses.append(f"{key}={value}") #: If it's a number, then don't include quotes indicating a string in the command
    if len(clauses) > 0:
        cmd += f" where {' and '.join(clauses)}"
#
# --- Fetch data
#
    print(cmd)
    result = conn.fetchall(cmd)
    return result
#
#--- convert none string data into string
#
    """
    save = []
    for dset in row:
        tsave = []
        for k in range(0, len(dset)):
            ent = dset[k]
#
#--- convert sybpydb.LOB objects are converted back to a string
#
            mc = re.search('LOB', str(ent))
            if mc is not None:
                out = convert_lob_to_string(cmd, k)
#
#--- convert datetime object into date
#
            elif isinstance(ent, datetime.date):
                out = ent.strftime('%Y-%m-%dT%H:%M:%S')

#            elif isinstance(ent, varchar):
#                out = str(ent)

            else:
                out = ent

            tsave.append(out)

        tsave = tuple(tsave)
        save.append(tsave)
#
#--- convert a list to a json string so that we can pass back to the main script
#
    #row = json.dumps(save, cls=JsonCustomEncoder)

    #return row
    return save
    """

#-------------------------------------------------------------------------------------
#-- convert_lob_to_string: rerun pybase command for a lob object and convert into a string
#-------------------------------------------------------------------------------------

def convert_lob_to_string(cmd, pos):
    """
    rerun pybase command for a lob object and convert into a string
    input:  cmd --- original pybase command
            pos --- the position of lob object in the command column names
    output: out --- a content of lob
    """
#
#--- reconstruct the command for the lob object
#
    atemp = re.split('select', cmd)
    btemp = re.split('from',   atemp[1])
    ctemp = re.split(',',      btemp[0])
    col   = ctemp[pos]
    
    cmd   = 'select ' + col + ' from ' + btemp[1]
#
#--- return the sybase command
#
    conn = sqsh.Sqsh(dbi='sybase', server=_SERV, database = db, user = _USR, authdir = _AUTHDIR)
    row = conn.fetchone(cmd)
#
#--- convert lob object to a string
#
    out  = getlobdata(row[0])

    cur.close()
    conn.close()

    return out

#-------------------------------------------------------------------------------------
#-- getlobdata: convert LOB object to a string                                      --
#-------------------------------------------------------------------------------------

def getlobdata(lob):
    """
    convert LOB object to a string. 
    input:  lob --- LOB object
    output: out --- a string

    this functioin works only when LOB object is extracted specificlly for that column
    with fetchone. See "convert_lob_to_string" how to set to use this function.

    ref: http://infocenter.sybase.com/help/index.jsp?topic=/com.sybase.infocenter.dc20155.1600/doc/html/adh1376805082896.html
    """
    outarr = bytearray()
    chunk = bytearray(1024)
    while True:
        clen = lob.readinto(chunk)
        if clen == None:
            break

        outarr.extend(chunk[:clen])

    out = str(outarr)

    return out


#-------------------------------------------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) == 2:
        cmd = sys.argv[1]
        db  = 'axafocat'

    elif len(sys.argv) == 3:
        cmd = sys.argv[1]
        db  = sys.argv[2]

#    else:
#        print("Usage: get_value_from_sybase.py '<cmd>' <database name>")
#        print("If <database name> is not given, default is axafocat.")
#        print("(Don't forget '' around Sybase command.)")


    obsid = '23573'
    cmd = "select obsid,targid,seq_nbr,targname  from target where obsid=" + str(obsid) 
    #cmd = "select si_mode  from target where obsid=24573"
    #cmd = " select last from view_pi where ocat_propid=22200641"
    #cmd = 'select distinct pre_id from target where pre_id=10030'
    #cmd = 'select distinct pre_id from target where pre_id=10092'
    #cmd = 'select obsid from target where group_id=PKS2155_10700928'
    cmd = "select type, instrument  from target where obsid=" + str(obsid) 
    print("I AM HERE: " + cmd)
    db    = 'axafocat'
    out = get_value_from_sybase(cmd, db)
#
#---- this will return binay-like string
#
    print(out[0][0], out[0][1])
