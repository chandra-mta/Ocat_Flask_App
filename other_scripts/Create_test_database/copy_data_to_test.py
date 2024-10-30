#!/proj/sot/ska3/flight/bin/python

#
# --- copy_data_to_test.py: copying the data to the test directory
# --- author: W. Aaron (william.aaron@cfa.harvard.edu)
# --- last update: Oct 17, 2024
#

import os
import sqlite3 as sq
from contextlib import closing

OCAT_DIR = "/data/mta4/CUS/www/Usint/ocat"
COPY_DIR = "/proj/web-cxc/cgi-gen/mta/Obscat/ocat"
LIVE_DB = f"{OCAT_DIR}/updates_table.db"
TEST_DB = f"{COPY_DIR}/updates_table.db"

#
# --- Determine differences in individual parameter revision files
#
with closing(sq.connect(LIVE_DB)) as conn:  # Auto-closes
    with conn:  # Auto-commits
        with closing(conn.cursor()) as cur:  # Auto-closes
            live_fetch = cur.execute("SELECT obsidrev, rev_time FROM revisions").fetchall()
set_live = set(live_fetch)

if os.path.exists(TEST_DB):
    with closing(sq.connect(TEST_DB)) as conn:  # Auto-closes
        with conn:  # Auto-commits
            with closing(conn.cursor()) as cur:  # Auto-closes
                test_fetch = cur.execute("SELECT obsidrev, rev_time FROM revisions").fetchall()
    set_test = set(test_fetch)
else:
    raise Exception(f"Cannot find existing TEST_DB {TEST_DB} for updates comparison.")

changed_in_test = set_test - set_live
recent_live_revisions = set_live - set_test

#
# --- Remove individual parameter revision files located only in the test database
#
for entry in changed_in_test:
    os.system(f"rm -rf {COPY_DIR}/updates/{entry[0]}")
#
# --- Copy over new individual parameter revision files
#
for entry in recent_live_revisions:
    os.system(f"cp -f --preserve=all {OCAT_DIR}/updates/{entry[0]} {COPY_DIR}/updates/")
#
# --- Copy the real database, approved list, TOO Schedule
#
os.system(f"cp -f --preserve=all {COPY_DIR}/updates_table.db {COPY_DIR}/updates_table.db~")
os.system(f"cp -f --preserve=all {COPY_DIR}/approved {COPY_DIR}/approved~")
os.system(f"cp -f --preserve=all {OCAT_DIR}/updates_table.db {COPY_DIR}/updates_table.db")
os.system(f"cp -f --preserve=all {OCAT_DIR}/approved {COPY_DIR}/approved")
os.system(f"cp -f --preserve=all {OCAT_DIR}/Info_save/too_contact_info/schedule  {COPY_DIR}/Info_save/too_contact_info/schedule")
os.system(f"cp -f --preserve=all {OCAT_DIR}/cdo_warning_list {COPY_DIR}/cdo_warning_list")