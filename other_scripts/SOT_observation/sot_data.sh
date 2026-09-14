#!/bin/ksh

#
# run the query in sot_data.sql and save the output in /data/mta4/obs_ss/sot_data.sql
#

export SYBASE
passwd=`cat /data/mta4/CUS/www/Usint/Pass_dir/.targpass_internal`
/usr/local/bin/sqsh -h -Umtaops_internal_web -Socatsqlsrv -P$passwd -s ^ -i /data/mta4/obs_ss/sot_data.sql -w2100