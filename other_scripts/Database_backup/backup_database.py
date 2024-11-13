#!/proj/sot/ska3/flight/bin/python

#
# --- backup_database.py: backup usint related databases
# --- author: w. aaron (william.aaron@cfa.harvard.edu)
# --- last update: Oct 25, 2024
#

import sys

sys.path.append("/data/mta4/Script/Python3.11/lib/python3.11/site-packages")
import os
from dotenv import dotenv_values
import glob
from datetime import datetime
import sqlite3 as sq
from contextlib import closing
import argparse
import getpass

TECH = "william.aaron@cfa.harvard.edu"
CC = "mtadude@cfa.harvard.edu"
CONFIG = dotenv_values("/data/mta4/CUS/Data/Env/.cxcweb-env")
USINT_DIR = CONFIG["USINT_DIR"]
OCAT_DIR = f"{USINT_DIR}/ocat"
BACKUP_DIR = f"{OCAT_DIR}/Backup"
NOW = datetime.now()
SEND_MAIL = True

# --------------------------------------------------------------------------------------
# -- backup_database: backup usint related databases                                  --
# --------------------------------------------------------------------------------------


def backup_database():
    """
    Backup Usint related databases
    input:  None
    output: Create a backup of updates_table.db and approved files
            Also send a warning email if there is some potential problems with database integrity,
            such as the newer version of the updates_table.db or approved files being over 5% smaller
    """
    if compare_size(f"{OCAT_DIR}/updates_table.db", f"{BACKUP_DIR}/updates_table.db"):
        os.system(
            f"cp -f --preserve=all {OCAT_DIR}/updates_table.db {BACKUP_DIR}/updates_table.db"
        )
    else:
        text = f"{OCAT_DIR}/updates_table.db file is over 5% smaller than back up in {BACKUP_DIR}.\n"
        text += "Please check the backup and live databases.\n"
        text += f"This message was sent to {TECH} and {CC}."
        send_mail(
            "Check Usint Backup: updates_table.db", text, {"TO": [TECH], "CC": [CC]}
        )

    if compare_size(f"{OCAT_DIR}/approved", f"{BACKUP_DIR}/approved"):
        os.system(f"cp -f --preserve=all {OCAT_DIR}/approved {BACKUP_DIR}/approved")
    else:
        text = f"{OCAT_DIR}/approved file is over 5% smaller than back up in {BACKUP_DIR}.\n"
        text += "Please check the backup and live databases.\n"
        text += f"This message was sent to {TECH} and {CC}."
        send_mail("Check Usint Backup: approved", text, {"TO": [TECH], "CC": [CC]})


# --------------------------------------------------------------------------------------
# -- compare_size: check the file size change                                         --
# --------------------------------------------------------------------------------------


def compare_size(old, new):
    """
    check the file size change. if the new file is more than 5% smaller than the last
    something may be wrong.
    input:  old --- old file
            new --- new file
    output: True/False   --- if something wrong, return True. If size comparison is fine, return False
    """
    if not os.path.exists(new):
        return True
    diff = os.path.getsize(new) - os.path.getsize(old)
    if diff < 0:
        chk = abs(diff) / os.path.getsize(old)
        if chk > 0.05:
            return False

    return True


# ---------------------------------------------------------------------------------------
# -- send_mail: sending email                                                          --
# ---------------------------------------------------------------------------------------


def send_mail(subject, text, address_dict):
    """
    sending email
    input:  subject      --- subject line
            test         --- text or template file of text
            address_dict --- email address dictionary
    output: email sent
    """
    message = ""
    message += f"TO:{','.join(address_dict['TO'])}\n"
    if "CC" in address_dict.keys():
        message += f"CC:{','.join(address_dict['CC'])}\n"
    if "BCC" in address_dict.keys():
        message += f"BCC:{','.join(address_dict['BCC'])}\n"

    message += f"Subject:{subject}\n"

    if os.path.isfile(text):
        with open(text) as f:
            message += f.read()
    else:
        message += f"{text}"
    if SEND_MAIL:
        os.system(f"echo '{message}' | /sbin/sendmail -t")
    else:
        print(message)


# --------------------------------------------------------------------------------------
# -- check_mismatch: check for discrepancy between revision files and updates_table.db--
# --------------------------------------------------------------------------------------
def check_mismatch():
    """
    check for discrepancy between revision file and updates_table.db
    input:  --- none, but read from updates_table.db and OCAT_DIR/updates
    output: --- notification emails if discrepancy has occured.
    """
    cutoff = int(NOW.strftime("%s")) - 3.156e7
    #
    # --- Work only with checking revision files in proper format
    #
    rev_list = glob.glob(f"{OCAT_DIR}/updates/*")
    rev_list.sort(key=os.path.getmtime)
    rev_list = [os.path.basename(x) for x in rev_list if os.path.getmtime(x) > cutoff]
    rev_set = set()
    for x in rev_list:
        #
        # --- If the file can be converted into a float, then it's in obsid.rev format
        #
        try:
            y = float(x)
            rev_set.add(y)
        except ValueError:
            pass

    #
    # --- Fetch revision in database which have rev_time (discarding known missing legacy files)
    #
    with closing(sq.connect(f"{OCAT_DIR}/updates_table.db")) as conn:  # Auto-closes
        with conn:  # Auto-commits
            with closing(conn.cursor()) as cur:  # Auto-closes
                fetch_result = cur.execute(
                    f"SELECT obsidrev FROM revisions WHERE rev_time > {cutoff} ORDER BY rev_time DESC"
                ).fetchall()
    updates_set = set([x[0] for x in fetch_result])

    missing_updates = rev_set - updates_set
    missing_rev = updates_set - rev_set
    if missing_updates != set():
        text = "The following revisions have revision files but are missing from the updates_table.\n"
        if len(missing_updates) > 30:
            missing_updates_file = (
                f"{BACKUP_DIR}/missing_updates_{NOW.strftime('%Y:%m:%d:%H:%M:%S')}"
            )
            text += f"Too many status entries are missing, recording list in {missing_updates_file}\n"
            with open(missing_updates_file, "w") as f:
                for i in missing_updates:
                    f.write(f"{i}\n")
        else:
            for i in missing_updates:
                text += f"{i}\n"
        text += "Please check the database integrity."
        send_mail("Check Missing Usint Status Entry", text, {"TO": [TECH], "CC": [CC]})

    if missing_rev != set():
        text = "The following revisions are present in the updates_table but are missing revision files.\n"
        if len(missing_updates) > 30:
            missing_rev_file = (
                f"{BACKUP_DIR}/missing_rev_{NOW.strftime('%Y:%m:%d:%H:%M:%S')}"
            )
            text += f"Too many revision files are missing, recording list in {missing_rev_file}\n"
            with open(missing_updates_file, "w") as f:
                for i in missing_updates:
                    f.write(f"{i}\n")
        else:
            for i in missing_updates:
                text += f"{i}\n"
        text += "Please check the database integrity."
        send_mail("Check Missing Usint Revision File", text, {"TO": [TECH], "CC": [CC]})


# --------------------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--mode",
        choices=["flight", "test"],
        required=True,
        help="Determine running mode.",
    )
    parser.add_argument(
        "-p",
        "--path",
        required=False,
        help="Directory path to determine output location of backups.",
    )
    args = parser.parse_args()
    #
    # --- Determine if running in test mode and change pathing if so
    #
    if args.mode == "test":
        #
        # --- Path output to same location as unit tests
        #
        SEND_MAIL = False
        BACKUP_DIR = f"{os.getcwd()}/test/outTest"
        os.makedirs(BACKUP_DIR, exist_ok=True)
        backup_database()
        check_mismatch()

    elif args.mode == "flight":
        #
        # --- Create a lock file and exit strategy in case of race conditions
        #
        name = os.path.basename(__file__).split(".")[0]
        user = getpass.getuser()
        if os.path.isfile(f"/tmp/{user}/{name}.lock"):
            sys.exit(
                f"Lock file exists as /tmp/{user}/{name}.lock. Process already running/errored out. Check calling scripts/cronjob/cronlog."
            )
        else:
            os.system(f"mkdir -p /tmp/{user}; touch /tmp/{user}/{name}.lock")

        backup_database()
        check_mismatch()

        #
        # --- Remove lock file once process is completed
        #
        os.system(f"rm /tmp/{user}/{name}.lock")
