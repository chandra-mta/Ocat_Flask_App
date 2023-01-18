#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#########################################################################################
#													                                    #
#       convert_updates_table.py: modify the database and add hrc si column             #
#													                                    #
#		    author: t. isobe (tisobe@cfa.harvard.edu)	                                #
#													                                    #
#		    last update: Jun 23, 2021								                    #
#													                                    #
#########################################################################################

import sys
import os
import string
import re

sys.path.append('/data/mta/Script/Python3.8/Sybase/')
import get_value_from_sybase    as gvfs

#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------

def convert_updates_table():

    ifile = '/data/mta4/CUS/www/Usint/ocat/updates_table.list'
    with open(ifile, 'r') as f:
        data = [line.strip() for line in f.readlines()]

    line  = ''
    for ent in data:
        atemp = re.split('\t+', ent)
        alen  = len(atemp)
        if alen < 6:
            continue
        else:
#
#--- find instrument for this obsid
#
            btemp = re.split('\.', atemp[0])
            obsid = btemp[0]
            cmd   = 'select instrument from target where obsid=' + obsid
            out   = gvfs.get_value_from_sybase(cmd)

            mc    = re.search('acis', out.lower())
            if mc is not None:
                inst = 'acis'
            else:
                inst = 'hrc'

            line = line + atemp[0] + '\t'
            line = line + atemp[1] + '\t'
            line = line + atemp[2] + '\t'
#
#--- if the original si mode is not NULL, check which instrument is used
#
            if atemp[3] != 'NULL':
                if inst == 'acis':
                    line = line + atemp[3] + '\t'
                    line = line + 'NULL'   + '\t'
                elif inst == 'hrc':
                    line = line + 'NULL'   + '\t'
                    line = line + atemp[3] + '\t'
                else:
                    line = line + atemp[3] + '\t'
                    line = line + 'NULL'   + '\t'
            else:
                line = line + atemp[3] + '\t'
                line = line + 'NULL'   + '\t'

            line = line + atemp[4] + '\t'
            line = line + atemp[5] + '\t'
            if alen == 7:
                line = line + atemp[6] + '\n'
            else:
                line = line + '\n'

    with open('updates_table_n.list', 'w') as fo:
        fo.write(line)

#--------------------------------------------------------------------------------

if __name__ == "__main__":

    convert_updates_table()

