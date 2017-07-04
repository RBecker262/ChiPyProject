"""
masterbuild.py
Author: Robert Becker
Date: May 19, 2017
Purpose: submits all three processes to create daily master files for today
         can be used to execute processes to catchup from given date to today

Establish game date to update master files or a date range to rebuild them
Call function to build the daily schedule for each date
Call team and player master functions to update info for all games on each date
"""


import sys
import os
import argparse
import logging
import logging.config
import datetime
import time
import dailysched
import updteam
import updplayer


# setup global variables
LOGGING_INI = 'backend_logging.ini'


def init_logger(ini_path):
    """
    :param ini_path: path to ini files

    initialize global variable logger and setup log
    """

    global logger

    log_ini_file = ini_path + LOGGING_INI

    logging.config.fileConfig(log_ini_file, disable_existing_loggers=False)
    logger = logging.getLogger(os.path.basename(__file__))


def get_command_arguments():
    """
    -d or --date  optional, extract schedules for this date to current date
    -p of --path  optional, provides path of all ini files (must end with /)
    """

    parser = argparse.ArgumentParser('Command line arguments')
    parser.add_argument(
        '-d',
        '--date',
        help='Date of daily schedule for input - mm-dd-yyyy format',
        dest='game_date',
        type=str)
    parser.add_argument(
        '-p',
        '--path',
        help='Path for all ini files',
        dest='ini_path',
        type=str)

    argue = parser.parse_args()

    return argue


def establish_game_date(gamedate=None):
    """
    :param gamedate: date of the games in format "MM-DD-YYYY"

    If command line agrument not passed, use today's date
    create start and end dates of range, even if just processing today
    """

    # when today's date is used to calculate dates, subtract 6 hours to finish
    # getting data from yesterday's schedule for games ending after midnight.
    # allows master update process to run for current games until 6am next day
    if gamedate is None:
        gamedate = datetime.datetime.today()
        gamedate += datetime.timedelta(hours=-11)
        gamedate = gamedate.strftime("%m-%d-%Y")

    # start/end dates must be type datetime to get thru dates in range serially
    startdate = datetime.datetime.strptime(gamedate, "%m-%d-%Y")

    enddate = datetime.datetime.today()
    enddate += datetime.timedelta(hours=-11)
    enddate = enddate.replace(hour=0, minute=0, second=0, microsecond=0)

    logger.info('Updating master files from ' + gamedate + ' thru current day')

    return (startdate, enddate)


def main(gamedate, arg_path):

    if arg_path is None:
        ini_path = ''
    else:
        ini_path = arg_path

    init_logger(ini_path)

    dates = establish_game_date(gamedate)
    currentdate = dates[0]
    enddate = dates[1]

    # loop to process all games from start date through today's games
    while currentdate <= enddate:

        # set current date to proper format for function command line args
        date_of_game = currentdate.strftime("%m-%d-%Y")
        logger.info('---------------------------------------')
        logger.info('Building schedule and master files for: ' + date_of_game)

        # create the daily schedule for the given date
        rc = dailysched.invoke_dailysched_as_sub(date_of_game, arg_path)

        # rc 0 from dailysched - everything is perfect
        # rc 20 from dailysched - master scoreboard not ready yet, this is ok
        # anything else is critical error and process needs to stop
        if rc not in (0, 20):
            return rc

        # if the date's schedule is good then update master files
        if rc == 0:
            # update team master
            rc = updteam.invoke_updteam_as_sub(date_of_game, arg_path)
            if rc != 0:
                return rc

            # update player master
            rc = updplayer.invoke_updplayer_as_sub(date_of_game, arg_path)
            if rc != 0:
                return rc

        # sleep 5 seconds to avoid throttle from MLB only when running catchup
        if currentdate < enddate:
            logger.info('Sleeping 5 seconds.....')
            time.sleep(5)

        # bump the current date up by 1 day
        currentdate += datetime.timedelta(days=1)

    return rc


if __name__ == '__main__':

    args = get_command_arguments()

    cc = main(args.game_date, args.ini_path)

    logger.info('Script completion code: ' + str(cc))
    sys.exit(cc)
