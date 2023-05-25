#!/proj/sot/ska3/flight/bin/python -E

import sys
import os
import sqlite3

ifile = "/data/mta4/CUS/www/.groups"

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

with open(ifile, 'r') as f:
    data = [line.strip() for line in f.readlines()]

k = 0
member_dict = dict()
member_dict['testUSINT'] = {'id': k, 'name': 'testUSINT', 'mail': 'william.aaron@cfa.harvard.edu', 'groups':['test']}#includes test user

for ent in data:
    atemp = [a.strip() for a in ent.split(':')]
    #print(f"File line data: {atemp}")
    if (len(atemp) == 2) and (atemp[0][0] !='#') and (atemp[1] != ''): #cleanup for comments, ill-formated lines, or empty groups in .groups file
        groupname = atemp[0]
        grouplist = atemp[1].split()
        #print(f"Group: {groupname}")
        for member in grouplist:
            #print(f"Member: {member}")
            if member in member_dict: #already seen this member.
                member_dict[member]['groups'].append(groupname)
                #print("Already found member")
                #print(f"Info: {member_dict[member]}")
            else:
                k+=1
                member_dict[member] = {'id': k, 'name': member, 'mail': find_email(member), 'groups': [groupname]}
                #print(f"Info: {member_dict[member]}")

#print("Full members dictionary")
#print(member_dict)
#Creating SQL table

con = sqlite3.connect('app.db')
cur = con.cursor()

usr_table = """
CREATE TABLE User(
id interger PRIMARY Key,
username    string(64) NOT NULL,
email       string(64) NOT NULL,
groups_string   string(64) NOT NULL)"""

cur.execute(usr_table)
for member, info in member_dict.items():
    user_sql= "INSERT INTO User (id, username, email, groups_string) VALUES(?,?,?,?)"
    groups_string = ':'.join(info['groups'])
    cur.execute(user_sql,(info['id'], info['name'], info['mail'], groups_string))
con.commit()