#!/usr/bin/env /data/mta/Script/Python3.8/envs/ska3-shiny/bin/python

#########################################################################################
#                                                                                       #
#       update_user_database.py: create user name/email sqlite database                 #
#                                                                                       #
#           author: t.isobe (tisobe@cfa.harvard.edu)                                    #
#                                                                                       #
#           last update: May 26, 2021                                                   #
#                                                                                       #
#########################################################################################

import re
import sys
import os
import sqlite3

cmd = 'mv -f app.db app.db~'
os.system(cmd)

with open('/data/mta4/CUS/www/Usint/Pass_dir/usint_users', 'r') as f:
    data = [line.strip() for line in f.readlines()]

id_list   = []
user_list = []
mail_list = []

k = 0
for ent in data:
    atemp = re.split('\s+', ent)
    k += 1
    id_list.append(k)
    user_list.append(atemp[0].strip())
    mail_list.append(atemp[1].strip())

dlen = len(id_list)

con = sqlite3.connect('app.db')
cur = con.cursor()

usr_table = """
CREATE TABLE User(
id interger PRIMARY Key,
username    string(64) NOT NULL,
email       string(64) NOT NULL)"""


#usr_table = """
#CREATE TABLE User(
#id interger PRIMARY Key,
#username    text NOT NULL,
#email       text NOT NULL)"""

cur.execute(usr_table)


for k in range(0, dlen):
    user_sql= "INSERT INTO User (id, username, email) VALUES(?,?,?)"
    cur.execute(user_sql, (id_list[k], user_list[k], mail_list[k]))

con.commit()
