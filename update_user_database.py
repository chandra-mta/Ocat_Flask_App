#!/proj/sot/ska3/flight/bin/python

import os
import sqlite3
import argparse

IFILE = "/data/mta4/CUS/www/.groups"
OUT_DIR = "/data/mta4/CUS/Data/Users"
ADMIN = 'william.aaron@cfa.harvard.edu'

def update_user_database():
    """
    Read the .groups file determining ldap authentication for the Ocat Flask app and 
    fill out the relevant user information for app.db
    input: none, but read groups from IFILE
    output: none, but fill our app.db
    """
#
#--- Generate dictionary of user information
#
    users_dict = read_groups(IFILE)
    users_dict = find_email(users_dict)
#    
#--- Creating SQL table
#
    #Save previous state
    os.system(f"cp -f {OUT_DIR}/app.db {OUT_DIR}/app.db~")

    #As designed by the Ocat Flask App, the user database must be named app.db
    con = sqlite3.connect(f"{OUT_DIR}/app.db")
    cur = con.cursor()

    #Drop possibly outdated info
    cur = cur.execute('DROP TABLE IF EXISTS User')


    table = """CREATE TABLE user (
                id INT PRIMARY KEY NOT NULL,
                username string(64) NOT NULL,
                email string(64) NOT NULL,
                groups_string string(64) NOT NULL);"""
    
    cur.execute(table)
    #Test user in ID 0
    cur.execute(f"INSERT INTO User VALUES ('0', 'testUSINT', '{ADMIN}', 'test');")
    for user, info in users_dict.items():
        cur.execute(f"INSERT INTO User VALUES ('{info['id']}', '{user}', '{info['email']}', '{info['groups_string']}');")
    con.commit()

def read_groups(ifile = IFILE):
    """
    Read an ldap .groups formatted file and return member dictionary
    input: ifile --- .groups file path
    output: users_dict --- dictionary of member information based on file.
    """
    with open(ifile, 'r') as f:
        data = [line.strip() for line in f.readlines() if line.strip() != '']
    
    k = 1 #ID number 0 saved for a test user added later
    users_dict = dict()
    
    for ent in data:
        atemp = [a.strip() for a in ent.split(':')]
        group = atemp[0]
        member_subset = atemp[1].split()
        for member in member_subset:
            if member not in users_dict.keys():
                #Unlisted member
                users_dict[member] = {'id': k, 'groups_string': group}
                k += 1
            else:
                #Listed member
                users_dict[member]['groups_string'] += f":{group}"
    
    return users_dict

def find_email(users_dict):
    """
    Input a email found trhough the getent command into a users information dictionary
    input: users_dict --- users dictionary keyed by username and values with id and groups_string
    output: users_dict --- users dictionary keyed by username and values with id and groups_string and email
    """
#
#--- Read the NameSwitch Library Alias Database
#
    search = [x.split(':') for x in os.popen(f'getent aliases').read().split('\n')]
    #Note that the email string will still contain whitespace which must be striped
    for ent in search:
        if ent[0] in users_dict.keys():
            users_dict[ent[0]]['email'] = ent[1].strip()
    return users_dict



if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    parser.add_argument("-p", "--path", required = False, help = "Determine path to a .groups file determining LDAP authentication groups.")
    parser.add_argument("-d", "--directory", required = False, help = "Determine path to a database directory for storing the application's app.db")
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