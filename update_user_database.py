#!/proj/sot/ska3/flight/bin/python

import os
import sqlite3
import argparse

IFILE = "/data/mta4/CUS/www/.groups"
OUT_DIR = "/data/mta4/CUS/Data/Users"

search = os.popen(f'getent aliases').read().split('\n')


def find_email(member):
    for result in search:
        atemp = [a.strip() for a in result.split(':')]
        if atemp[0] == member:
            return atemp[1] #email string
    raise RuntimeError('find_email did not find member email in getent aliases\n')
    return None

with open(IFILE, 'r') as f:
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

#Creating SQL table

con = sqlite3.connect('tmp.db')
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

cmd = "rm app.db; mv tmp.db app.db"
os.system(cmd)


def update_user_database():
    """
    Read the .groups file determining ldap authentication for the Ocat Flask app and 
    fill out the relevant user information for it.
    """

    #Save previous state
    os.system(f"cp -f {OUT_DIR}/app.db {OUT_DIR}/app.db~")
    con.commit()

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-p", "--path", required = False, help = "Determine path to a .groups file determining ldap authentication groups.")
    parser.add_argument("-d", "--directory", required = False, help = "Determine path to a database directory for sotirng the applications app.db")
    args = parser.parse_args()
#
#--- Determine if running in test mode and change pathing if so
#
    if args.mode == "test":
        if args.path:
            IFILE = args.path
        else:
            IFILE = f"{os.getcwd()}/.groups"
        if args.directory:
            OUT_DIR = args.directory
        else:
            OUT_DIR = f"{os.getcwd()}"

        update_user_database()
    else:
        update_user_database()