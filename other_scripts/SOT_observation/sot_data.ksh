#!/bin/ksh

#
# run the query in sot_data.sql and save the output in /data/mta4/obs_ss/sot_data.sql
#

#SYBASE=/soft/sybase
#SYBASE=/soft/SYBASE_OCS15
export SYBASE
passwd=`cat /data/mta4/MTA/data/.ocatpasswd`
/usr/local/bin/sqsh -h -Ubrowser -Socatsqlsrv -P$passwd -s ^ -i /data/mta4/obs_ss/sot_data.sql -w2100

