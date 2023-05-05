#!/proj/sot/ska3/flight/bin/python -E

import sys
import os
import sqlite3



def find_email(member):
    search = os.popen(f'getent aliases | grep {member}').read().split('\n')
    for result in search:
        atemp = [a.strip() for a in result.split(':')]
        if atemp[0] == member:
            return atemp[1] #email string
    raise RuntimeError('find_email did not find member email in getent aliases\n')
    return None



cmd = 'mv -f app.db app.db~'
os.system(cmd)

with open('/data/mta4/CUS/www/.groups', 'r') as f:
    data = [line.strip() for line in f.readlines()]

#Including a test user for the sake of development.

id_list    = [0]
user_list  = ['testUSINT']
mail_list  = ['william.aaron@cfa.harvard.edu']
group_list = ['test']

k = 0
for ent in data:#Must change
    print(ent)
    atemp = [a.strip() for a in ent.split(':')]
    #Cleanup
    if (len(atemp) == 2) and (atemp[0][0] !='#'): #cleanup for comments or ill-formated lines in .groups file
        groupname = atemp[0]
        groupmember = atemp[1].split()
        for member in groupmember:
            k += 1
            id_list.append(k)
            user_list.append(member)
            email = find_email(member)
            mail_list.append(email)
            group_list.append(groupname)

dlen = len(id_list)                                                                                                                                                                                  

con = sqlite3.connect('app.db')
cur = con.cursor()

usr_table = """
CREATE TABLE User(
id interger PRIMARY Key,
username    string(64) NOT NULL,
email       string(64) NOT NULL,
groupname   string(64) NOT NULL)"""


cur.execute(usr_table)

for k in range(0, dlen):
    user_sql= "INSERT INTO User (id, username, email, groupname) VALUES(?,?,?,?)"
    cur.execute(user_sql, (id_list[k], user_list[k], mail_list[k], group_list[k]))

con.commit() 

