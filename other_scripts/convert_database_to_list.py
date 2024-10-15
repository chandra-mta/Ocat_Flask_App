#!/proj/sot/ska3/flight/bin/python
#################################################################################
#                                                                               #
#       convert_database_to_list.py                                             #
#                                                                               #
#       author: w. aaron (william.aaron@cfa.harvard.edu)                        #
#                                                                               #
#       last update: Oct 15, 2024                                               #
#                                                                               #
#################################################################################
import os
import sqlite3 as sq
from contextlib import closing
import argparse

OCAT_DIR = "/data/mta4/CUS/www/Usint/ocat"
DATABASE_FILE = f"{OCAT_DIR}/updates_table.db"
LIST_FILE = f"{OCAT_DIR}/updates_table.list"


def convert_database_to_list():
    """
    Writes the SQLite database formatted contents of the updates_table.db file into the updates_table.list format
    Input: None but read from the DATABASE_FILE
    Output: None but write to the LIST_FILE
    """
    with closing(sq.connect(DATABASE_FILE)) as con: #Auto-closes connection
        with con: #Auto-commits database transactions.
            with closing(con.cursor()) as cur: #Auto-closes cursor
                fetch_result = cur.execute("SELECT * from revisions ORDER BY rev_time ASC").fetchall()
    with open(LIST_FILE, 'w') as f:
        for entry in fetch_result:
            out = convert_to_line(entry)
            f.write(f"{out}\n")

def convert_to_line(entry):
    """
    Formats an entry from the updates_table.db SQLite file into the updates_table.list format.
    Input: entry --- tuple of the following sqlite columns in order.
                     obsidrev (0), general_signoff (1), general_date (2), acis_signoff (3), acis_date (4),
                     acis_si_mode_signoff (5), acis_si_mode_date (6), hrc_si_mode_signoff (7), hrc_si_mode_date (8),
                     usint_verification (9), usint_date (10), sequence (11), submitter (12), rev_time (13) (creation of rev in epoch time)
    Output: string --- text file line formatted in the updates_table.list format
    """
#
#--- obsidrev
#
    string = f'{entry[0]}\t'
#
#--- general signoff
#
    if entry[1] == None or entry[1] == 'NA' or entry[1] == 'N/A':
        string += f'{entry[1]}\t'
    else:
        string += f'{entry[1]} {entry[2]}\t'
#
#--- acis signoff
#
    if entry[3] == None or entry[3] == 'NA' or entry[3] == 'N/A':
        string += f'{entry[3]}\t'
    else:
        string += f'{entry[3]} {entry[4]}\t'
#
#--- acis si mode signoff
#
    if entry[5] == None or entry[5] == 'NA' or entry[5] == 'N/A':
        string += f'{entry[5]}\t'
    else:
        string += f'{entry[5]} {entry[6]}\t'
#
#--- hrc si mode signoff
#
    if entry[7] == None or entry[7] == 'NA' or entry[7] == 'N/A':
        string += f'{entry[7]}\t'
    else:
        string += f'{entry[7]} {entry[8]}\t'
#
#--- verification
#
    if entry[9] == None or entry[9] == 'NA' or entry[9] == 'N/A':
        string += f'{entry[9]}\t'
    else:
        string += f'{entry[9]} {entry[10]}\t'
    string += f'{entry[11]}\t{entry[12]}'
#
#--- Replace all None portions of string with NULL
#
    string = string.replace('None',"NULL")
    return string


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices = ['flight','test'], required = True, help = "Determine running mode.")
    args = parser.parse_args()
#
#--- Determine if running in test mode and change pathing if so
#
    if args.mode == "test":
#
#--- Path input and output to the test revision database
#
        OCAT_DIR = "/proj/web-cxc/cgi-gen/mta/Obscat/ocat"
        DATABASE_FILE = f"{OCAT_DIR}/updates_table.db"
        LIST_FILE = f"{OCAT_DIR}/updates_table.list"
#
#--- For ease of testing setup, change the group of the updates_table.list file in case removed
#
        os.system(f"touch {LIST_FILE}; chgrp mtagroup {LIST_FILE}")
        convert_database_to_list()
    elif args.mode == "flight":
        convert_database_to_list()