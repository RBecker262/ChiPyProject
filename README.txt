ChiPy 2017 Spring Mentorship Project - MLB Gameday Data Retrieval

I’ve created a website in a cloud environment to take requests seeking up to the minute player statistics for games completed or even in progress, and displays that information back via the web pages provided.

Here is all of the setup needed to make the website run properly.


Back End Setup
==============
There are scripts that must run periodically throughout the day to create player and team master files containing the season data which also help drive retrieval to the real time data when getting today’s stats. To execute the process a single driver script can be run using the following command (scripts located in the backend folder):

python masterbuild.py

Config and logging ini files are used in this backend process and the module either assumes them to be in the same directory from where the module or shell script is executed (which is not necessarily the same location of the module or scripts themselves), or you can pass a command line argument indicating the path to where the ini files are located. If providing a path the command to execute the module would look something like this:

python masterbuild.py -p /opt/python/app/backend/

Copy the SAMPLE_backend_config.ini and SAMPLE_backend_logging.ini files to the directory where you want them located and drop the SAMPLE_ from the front of each file name giving you backend_config.ini and backend_logging.ini. All backend scripts share the same logging and config information, so one ini to rule them all. Remember to update your path in the command above.

As for schedule I am running this update process every two hours around the clock. The team and player master files hold an accumulation of seasonal data, and the team file also holds information regarding today’s games for each team. It just doesn’t change very often during the day as the only information updated in these files are game schedules as they become posted and seasonal stats after a game is completed.

Since we are in the middle of the season and the systems works better if the master files have data from opening day until now, a special one time run should be executed passing the date of opening day as a command line argument (this will run for a while to catch up), and of course provide your path to the ini files depending on where they are located:

python masterbuild.py -d 04-02-2017 -p /opt/python/app/backend/


Web Setup
=========
The web application must be tied in with a web server like Apache. The current setup has all web and API routing performed through a single application module, the long term goal is to split the API routing into its own server listening on a different port. For the current application setup however the server module is named thesandlot.py. Apache assumes the module name is application.py. To make this work you must change the WSGIPath configuration parameter to thesandlot.py in order for Apache to find and execute the correct module.

You will also likely need to set the Static file parameter to webapp/static/ to find all of the picture files to load into the web pages.
