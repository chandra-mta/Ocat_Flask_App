============================
Using Ocat Flask Application
============================

This repo contains the Python Flask application supporting the `Usint Website <https://cxc.cfa.harvard.edu/wsgi/cus/usint/>`_ as well as legacy Usint supporting non-Flask Python scripts.
For information related to the webserver backend and support and development of this application, consult the Flask/Usint folder in the MTA shared drive.

Structure
=========

* usint (and usint.py) --- Python script for instantiating the Flask application. Navigating to this file in a web browser starts the application.
* update_user_database.py --- Updates user database as stored in the /data/mta4/CUS/Data/Users directory.
* config.py --- Configuration file.
* localhost --- A tcsh shell script used for quickly starting a localhost test of the application by using the /data/mta4/CUS/ska3-cus-r2d2-v environment.
* other_scripts --- A directory to keep related non-Flask Python scripts which support legacy Usint purposes.
* logs --- A directory for containing ocat.log files for logging application running information. Used by web server processes.
* cus_app --- Main Flask application folder containing relevant page generation scripts.

  * __init__.py --- Setting functions.
  * email.py --- Email related functions.
  * model.py --- Setting models of users.
  * chkupdata --- A directory to keep checkupdata related scripts.
  * errors --- A directory to keep error handler related scripts.
  * express --- A directory to keep express signoff related scripts.
  * ocatdatapage --- A directory to keep ocat data page related scripts.
  * orupdate --- A directory to keep orupdate related scripts.
  * scheduler --- A directory to keep scheduler related scripts.
  * supple --- A directory to keep supplemental python scripts.
  * static:

    * color_list --- A list of color coding.
    * dir_list --- A list of directories used by scripts.
    * js --- A directory to keep JavaScript scripts.
    * no_plots.png --- A PNG file saying no plot.
    * ocat_style.css --- Ocat CSS style sheets.
    * param_list --- A list of parameters used in ocat related scripts.
    * ocatdatapage --- A directory to keep ocatdatapage related static files/HTML pages.
    * orupdate --- A directory to keep orupdate related static HTML page.
    * scheduler --- A directory to keep scheduler related static HTML page.
  * templates:

    * base.html --- A base HTML template.
    * index.html --- A main index page.
    * redirect.html --- A redirect page.
    * page-related templates --- these directories will be described in the page-specific sections below.

chkupdata
=========

Display all original/requested/current parameter values for a given <obsid>.<rev>.

* routes.py --- Main script.
* __init__.py --- Script to setup the function.

related scripts:
    
* supple/read_ocat_data.py

data:
    
* current_app.config['DATA_DIR']/updates/<obsid>.<rev>
* CXC Ocat Sybase database (via read_ocat_data.py)

templates:
    
* index.html --- Main page.
* display.html --- Page to display the parameter list.
* try_again.html --- Page to display the notice when <obsid>.<rev> is not found.
* macros.html --- Macro holder.

error
=====

Error handler.

* handlers.py --- Main script.
* __init__.py --- Script to setup the function.

data: None

templates:
    
* 404.html --- 404 error page.
* 500.html --- 500 error page.

express
=======

Express sign-off/approval page.

* routes.py --- Main script.
* __init__.py --- Script to setup the function.

related scripts:
    
* ocatdatapage/create_selection_dict.py
* ocatdatapage/update_data_record_file.py

data:
    
* current_app.config['DATA_DIR']/updates/<obsid>.<rev>
* current_app.config['DATA_DIR']/updates_table.db
* current_app.config['DATA_DIR']/approved
* CXC Ocat Sybase database (via read_ocat_data.py)

templates:
    
* index.html --- Main page.
* macros.html --- Macro holder.

ocatdatapage
============

Ocat data page to update the parameter values.

* routes.py --- Main script.
* __init__.py --- Script to setup the function.
* check_value_range.py --- Check whether the values are in the expected range.
* create_selection_dict.py --- Create a dict of p_id <--> [<p_id information>].
* send_notifications.py --- Sending out notifications.
* submit_other_obsids.py --- Update obsids on a list as the original obsid was updated.
* update_data_record_file.py --- Create a data record file for a given obsid.

related scripts:
    
* supple/read_ocat_data.py
* email.py

data:
    
* current_app.config['DATA_DIR']/updates/<obsid>.<rev>
* current_app.config['DATA_DIR']/updates_table.db
* current_app.config['DATA_DIR']/approved
* CXC Ocat Sybase database (via read_ocat_data.py)
* <obs_ss>/mp_long_term --- Planned roll angle from MP site.
* <obs_ss>/scheduled_obs_list --- Scheduled obsids.

templates:
    
* index.html --- Main page/parameter value update page.
* display_parameters.html --- Updated parameter value check page.
* finalize.html --- Page to display the job complete notification.
* provide_obsid.html --- Page to display <obsid> if it was not found.
* macros.html --- Macro holder.

orupdate
========

Target parameter status page.

* routes.py --- Main script.
* __init__.py --- Script to setup the function.

related scripts:
    
* supple/get_value_from_sybase.py
* ocatdatapage/create_selection_dict.py
* ocatdatapage/update_data_record_file.py

data:
    
* current_app.config['DATA_DIR']/updates/<obsid>.<rev>
* current_app.config['DATA_DIR']/updates_table.db
* current_app.config['DATA_DIR']/approved
* CXC Ocat Sybase database (via read_ocat_data.py)

templates:
    
* index.html --- Main page.
* macros.html --- Macro holder.

The page is refreshed every 3 minutes to display the most recent data. This is done because multiple users can be updating the databases and someone else might update them while a user tries to update the database.

rm_submission
=============

Remove an accidental submission.

* routes.py --- Main script.
* __init__.py --- Script to setup the function.

data:
    
* current_app.config['DATA_DIR']/updates/<obsid>.<rev>
* current_app.config['DATA_DIR']/updates_table.db
* current_app.config['DATA_DIR']/approved

templates:
    
* index.html --- Main page.
* macros.html --- Macro holder.

scheduler
=========

POC duty sign-up sheet.

* routes.py --- Main script.
* read_poc_schedule.py --- Script to read the schedule database and create a data table.
* __init__.py --- Script to setup the function.

related scripts:
    
* other_scripts/create_schedule_table.py
* other_scripts/write_this_week_too_poc.py

data:

* current_app.config['INFO_DIR']/schedule

templates:

* index.html --- Main page.
* macros.html --- Macro holder.

supple
======

Provide supplemental scripts used by several groups.

* get_value_from_sybase.py --- Script to access CXC Ocat Sybase database and read data values.
* ocat_common_functions.py --- Collection of functions used by other scripts.
* read_ocat_data.py --- Script to extract all parameter values for a given obsid.

other scripts
=============

This directory keeps non-Flask Python scripts which support legacy Usint uses.

* create_schedule_table.py --- Create a static HTML and send out notifications.
* write_this_week_too_poc.py --- Write out the current POC at /home/mta/TOO-POC.

related scripts
===============

Scripts which create data used by this set of Flask scripts.

in /data/mta4/obs_ss/
---------------------
* find_planned_roll.py --- Find roll angles.
* find_scheduled_obs.py --- Find scheduled observations.

in /data/mta4/CUS/www/Usint/
----------------------------
* create_schedule_table.py --- Create POC duty table HTML/send POC duty notification.
* signoff_request.py --- Send out sign-off request.
* check_hrc_si_mode_sign_off.py --- Check HRC SI mode sign-off status.

in /data/mta4/CUS/www/Usint/Too_Obs
-----------------------------------
* too_ddt_update.py --- Check TOO/DDT observations and update related information.

Live Data
=========

Active databases are located in: /data/mta4/CUS/www/Usint/ocat/

* approved --- A list of approved obsid.

  * <obsid> <seq #> <poc> <date of approved>

* updates_table.db --- A SQLite Database of sign-off status.

  * <obsid>.<rev>
  * <general sign-off status>
  * <general sign-off date>
  * <acis sign-off status>
  * <acis sign-off date>
  * <acis si sign-off status>
  * <acis si sign-off date>
  * <hrc si sign-off status>
  * <hrc si sign-off status>
  * <usint verification status>
  * <usint verification date>
  * <seq #>
  * <submitter>
  * <epoch time of creation of revision>
  * NULL --- The column does
