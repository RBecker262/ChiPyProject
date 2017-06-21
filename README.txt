ChiPy 2017 Spring Mentorship Project - MLB Gameday Data Retrieval

I am creating services in a cloud environment to take requests seeking up to the minute player data as games progress, and send that info back to the requesting site or app.

Here is all of the setup needed to make the website run properly.


Back End Setup
==============
There are scripts that must run periodically throughout the day to create player and team master files that contain season data and help drive retrieval to real time data when getting today’s stats. To run the process a single driver script can be run using the following command:

Scripts are located in the /backend folder.

python masterbuild.py

As for schedule, since the instance where this runs is located in the Eastern time zone, it should run every half hour from noon today to 5am the next morning. This accounts for both early afternoon games as well as those extra inning west coast night games that go well past midnight.

Since we are in the middle of the season and the systems works better if the masters have data from opening day until now, a special one time run should be executed passing the date of opening day as a command line argument (this will run for a while to catch up):

python masterbuild.py -d 04-02-2017


Web Setup
=========
The web and api servers must be brought up to handle the HTTP requests. The web server will run using port 80 as it needs to be open to the outside world. The api server must run using a different port, preferably an internal port (1 - 1023) as these are not public API’s. The web server will receive an initial request to display a web page, and the code behind it will make api requests using endpoints to the api server through the appropriate internal port. To bring up these servers enter these commands two commands:

Scripts are located in the root project folder.

Web Server
python thesandlot.py

API server
python api_server.py

Both will log messages for every HTTP request each receives.


