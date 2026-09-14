A bash script to run sot_data.sql and
the sql script obtains specified column values from database from all data
and put into two data files.

This is a slim-down version of /data/udoc2/targets/joh.sql, specifically made
for SOT/USINT use. Only columns needed for sot_answer.cgi are extracted.


Dir: /data/mta4/obs_ss/ 
Legacy Documentation: https://cxc.cfa.harvard.edu/mta_days/mta_script_list/USINT/ti_sot_observations.html

Scripts:
--------
sot_data.sh
sot_data.sql


Data:
-----
Sybase access
Needs ocat authentication login located at /data/mta4/CUS/authorization

Output:
-------

/data/mta4/obs_ss/sot_ocat.out
/data/mta4/obs_ss/sot_ocat_ra.out

Cron job:
---------
c3pov-v as mta
30 * * * * cd /data/mta4/obs_ss/; /data/mta4/obs_ss/sot_data.sh >> $HOME/Logs/sot_data.cron 


